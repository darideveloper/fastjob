# Design Notes: harden-unsubscribe-flow

## Why this needs a design doc

The change touches three subsystems (HTTP view, mail engine, importer) and introduces a contract change to the unsubscribe URL. RFC 8058 (one-click) plus CSRF makes the GET-vs-POST split slightly subtle, and the Gmail/Graph header injection differs between the two send paths. Capturing the trade-offs here keeps the spec deltas focused on observable behaviour.

## Architectural decisions

### 1. GET shows a form; POST commits the unsubscribe

**Problem.** Email clients pre-fetch URLs to render previews and run AV scans. Pre-fetched URLs that mutate state are silently triggered before the human reads the message. Today's `unsubscribe(request, token)` is a GET that calls `Blacklist.objects.get_or_create(...)` — every Outlook Safe Links scan blacklists the company.

**Decision.** Keep the URL stable (`/unsubscribe/<uuid:token>/`) and split the view by method:
- `GET` → render `unsubscribe_confirm.html` with a CSRF-protected `<form method="post" action="">`.
- `POST` → insert / refresh the `Blacklist` row, mark `MailingLog.unsubscribed_at = now()`, render `unsubscribe.html` (success page).

**Why one URL instead of two.** RFC 8058 mandates the one-click POST target be the same URL the user lands on; splitting `/unsubscribe-confirm/` and `/unsubscribe-commit/` would force two `List-Unsubscribe` URLs and complicate the email body. One URL, two methods is the standard pattern.

### 2. CSRF exemption for the unsubscribe POST

**Problem.** The recipient (a company) is not authenticated to FastJob — they have no session, no CSRF cookie, no way to acquire one. Standard Django CSRF would block the POST.

**Decision.** Apply `@csrf_exempt` to the POST handler. The unsubscribe token in the URL is the authentication factor: it is a UUID4, unique-indexed, and known only to the recipient who received the email. This is the same security model used for password-reset links, S3 presigned URLs, and the existing `cv_download` view.

**Audit countermeasure.** Keep the per-IP rate limit (10/h, currently in `views.py:64`). Combined with the UUID, this defeats both scanner pre-fetch (which doesn't issue POSTs) and brute force (10/h × 3.4×10³⁸ token space).

### 3. List-Unsubscribe headers — Gmail vs Microsoft Graph

**Gmail path** (`_send_via_gmail`) builds raw RFC 822 MIME and base64url-encodes it. We add the headers directly:
```
List-Unsubscribe: <https://fastjob.example/unsubscribe/{token}/>, <mailto:unsubscribe@fastjob.example?subject=unsubscribe-{token}>
List-Unsubscribe-Post: List-Unsubscribe=One-Click
```
The `mailto:` form requires a real inbox to receive bounces. We will reuse `DEFAULT_FROM_EMAIL` host and route the inbox to a Celery handler in a follow-up change; for now the URL form is the primary mechanism and the `mailto:` is informational.

**Microsoft Graph path** (`_send_via_microsoft`). Graph's `sendMail` API requires custom headers in `internetMessageHeaders`, and historically required the `x-` prefix. Per current Microsoft docs (≥ Graph v1.0, 2023+), `List-Unsubscribe` and `List-Unsubscribe-Post` are explicitly whitelisted without the prefix. If a future API version regresses, the fallback is to send the headers as `x-list-unsubscribe` and accept the slight deliverability cost.

### 4. CV download blacklist gate

**Decision.** Before generating the presigned S3 URL in `cv_download`, look up `Blacklist.objects.filter(email=log.company_email_snapshot).exists()`. If true, return `410 Gone` with a short HTML page (`cv_revoked.html`) explaining the link has been revoked.

**Why not 404?** 404 implies the link never existed, which leaks no information but feels wrong to the (rare) accidental click after legitimate unsubscribe. 410 is the semantically correct answer: "this resource is gone permanently, do not retry."

**Performance.** One indexed exists() query per CV download. Negligible.

### 5. Importer reporting

**Decision.** Add a counter inside `import_companies_from_xlsx`:
```
blacklisted_set = set(Blacklist.objects.values_list("email", flat=True))
# ...
if email in blacklisted_set:
    blacklisted_skipped += 1
# (still update_or_create — we want the row in case the blacklist row is later removed)
```
Return `(created, updated, errors, blacklisted_skipped)`.

**Why still write the Company row.** Two reasons:
1. If an admin later legitimately removes a row from `Blacklist` (e.g. a wrong-address request), we don't want to discover that the company record is also missing.
2. The blacklist already gates sending. Suppressing the import row would be redundant policy in two places.

**Storage of the new counter on `CompanyImportBatch`.** Two options:
- **(A)** Add a dedicated column `blacklisted_skipped IntegerField default=0`. Pro: queryable, easy to surface in admin. Con: schema migration.
- **(B)** Stash it inside the existing `error_log` JSON / text field. Pro: zero migration. Con: no admin column.

**Choice: (A).** The migration is additive and zero-risk; queryability matters because operators want to scan recent imports for unusually high blacklist hit rates (signal of an abused list).

### 6. New `MailingLog.unsubscribed_at`

**Decision.** Nullable `DateTimeField`, set when the POST handler successfully writes the `Blacklist` row. Lets us answer "which user's send / which template generated this opt-out?" without joining log history to blacklist insertion timestamps approximately.

**Alternative considered.** A separate `UnsubscribeEvent` model. Rejected as YAGNI — the FK to `MailingLog` already gives us user, company, template, and time-of-send; one nullable timestamp is enough.

### 7. Lowercase / strip on `Blacklist.add()`

**Decision.** Add a classmethod:
```python
@classmethod
def add(cls, email, reason="unsubscribe"):
    normalized = (email or "").strip().lower()
    if not normalized:
        raise ValueError("empty email")
    return cls.objects.get_or_create(
        email=normalized,
        defaults={"reason": reason, "added_at": timezone.now()},
    )
```
Replaces all `Blacklist.objects.get_or_create(email=...)` callsites (currently only `views.py`). Closes the latent case-sensitivity gap and provides a single audit point.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Scanners that issue POST as well as GET (rare; corporate "click through" sandboxes) | The one-click POST is a deliberate accept; the rate limit (10/h/IP) caps damage. We accept this — it's the contract RFC 8058 defines. |
| Existing `Blacklist` rows with mixed casing (legacy data) cause duplicate inserts on rewrite | Run a one-shot data migration that lowercases all existing `Blacklist.email` values; conflict on the unique constraint is resolved by keeping the earliest `added_at`. |
| Microsoft Graph rejects the unprefixed header in some tenant configs | Fall back to `x-list-unsubscribe` / `x-list-unsubscribe-post` on `400` responses; log the fallback once per process. |
| Operators relying on the old GET-mutates contract (e.g. internal scripts that "unsubscribe by hitting the URL") | Document the change in the deploy notes; offer a Django admin action `Add to blacklist` for manual operator workflows. |

## Things explicitly NOT changing

- The `Blacklist` model schema (no per-company FK, no per-user scope).
- The slow-drip beat cadence and the `blacklisted_emails` set materialisation.
- The `cv_download` rate limit, token lifetime, presigned URL TTL.
- The unsubscribe URL path itself (`/unsubscribe/<uuid:token>/`).
