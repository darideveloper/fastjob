# Change: Harden the Blacklist / Unsubscribe Flow

## Why

The blacklist (one-way opt-out by company email) is the single mechanism that protects the platform's deliverability reputation and complies with Spanish/EU anti-spam law (LSSI-CE Art. 21–22, GDPR Art. 21). Audit of the current implementation surfaced one **high-severity functional bug** and several smaller gaps:

1. **Silent auto-unsubscribes from email-client link pre-fetch.** `apps/mailing/views.py:65` is a plain `GET` that mutates state. Outlook Safe Links, Gmail's link scanner, corporate proxy AV, and Microsoft Defender all routinely pre-fetch every URL inside an incoming message to render previews and check for malware. Each pre-fetch silently inserts a `Blacklist` row before the human ever sees the email — destroying the recipient pool for no reason and giving us no way to distinguish a real opt-out from a scanner artefact.

2. **Missing `List-Unsubscribe` / `List-Unsubscribe-Post` headers.** Since February 2024, Gmail and Yahoo's bulk-sender requirements mandate RFC 2369 / RFC 8058 headers for any sender that crosses 5 000 messages/day to their domains. Even at lower volume, mailbox providers boost spam scoring without these headers. `apps/mailing/engine.py` (Gmail and Microsoft Graph paths) does not emit them today.

3. **`cv_download` does not honour the blacklist.** A recipient who has opted out can still hit a previously delivered CV link. Most operators expect "unsubscribe" to be a hard cut.

4. **Importer is blind to the blacklist.** `apps/companies/importers.py` happily upserts companies whose email is already in `Blacklist`. The mailer correctly skips them at send time, but the admin sees `created=N` with no signal that some are dead-on-arrival, which produces misleading capacity counts on the dashboard.

5. **Case-sensitivity gap in `get_or_create`.** `apps/mailing/views.py:75` does `Blacklist.objects.get_or_create(email=email, …)`. `LowercaseFieldsMixin` lowercases on `save()` only — the `get` phase queries with the value as-is. In practice `company_email_snapshot` is lowercase, so this is latent rather than active, but it is a class of bug worth closing.

6. **No tests for the unsubscribe view.** `apps/mailing/tests/test_views.py` covers `cv_download` only; the blacklist write path has zero coverage.

## What Changes

### Behavioural changes
- **BREAKING** (URL contract): `GET /unsubscribe/<token>/` no longer mutates state. It now renders an interstitial page with a confirmation `<form method="post">` and a CSRF token. The `Blacklist` row is created only on `POST` to the same URL.
- A `List-Unsubscribe` header AND a `List-Unsubscribe-Post: List-Unsubscribe=One-Click` header are added to every outgoing CV email (Gmail and Microsoft Graph paths). The `List-Unsubscribe` value is `<{unsubscribe_url}>, <mailto:{unsubscribe_mailbox}?subject=unsubscribe>` per RFC 2369; the URL form is the primary mechanism, the `mailto:` is a fallback. RFC 8058 one-click POST is honoured by the same view that handles the human form.
- `GET /cv/<token>/` (the CV download view) returns `410 Gone` when the recipient's email is in the blacklist. The presigned S3 URL is never generated for an opted-out address.
- The XLSX importer counts and reports `blacklisted_skipped` rows in addition to `created` / `updated`. Blacklisted emails are still written to `Company` (so the row exists for future re-imports if they are ever removed from the blacklist), but the import-batch record exposes the count so the admin sees the real ingest impact.
- `Blacklist.objects.get_or_create(...)` calls are normalised: the email is `.lower().strip()`-ed before the lookup. A safety method `Blacklist.add(email, reason="unsubscribe")` encapsulates this.

### Non-behavioural / observability changes
- New `MailingLog.unsubscribed_at` (nullable `DateTimeField`) records when a particular log triggered an unsubscribe, so we can correlate which template / which user's send caused each opt-out (today the `Blacklist` row only stores the email).
- Structured log line on every successful unsubscribe POST: `{outcome: "unsubscribed", user_pk, company_email_hash, template_id, log_pk}`. The email is hashed (sha256) — never logged in clear text — so the log retains analytical value without leaking PII.
- The unsubscribe interstitial template (`templates/mailing/unsubscribe_confirm.html`) is added; the existing `unsubscribe.html` is repurposed as the post-POST success page.

### Test additions
- `test_views.py::test_unsubscribe_get_does_not_blacklist`
- `test_views.py::test_unsubscribe_post_blacklists_and_is_idempotent`
- `test_views.py::test_unsubscribe_post_one_click_without_csrf` (RFC 8058 says one-click POST must succeed without an interactive CSRF token; we exempt the view via `@csrf_exempt` but require the unsubscribe token in the URL to authenticate the request)
- `test_views.py::test_unsubscribe_invalid_token_returns_404`
- `test_views.py::test_cv_download_blocked_after_unsubscribe`
- `test_engine.py::test_send_emits_list_unsubscribe_headers_gmail`
- `test_engine.py::test_send_emits_list_unsubscribe_headers_outlook`

## Impact

- **Affected specs:**
  - `mailing` — adds a new "Unsubscribe and Blacklist Enforcement" requirement (with sub-scenarios for the two-step flow, the one-click POST, the headers, the CV gate, and the structured log) and a "Unsubscribe Email Headers" requirement.
  - `companies` — modifies the existing "Enhanced Spanish XLSX Importer" requirement to surface `blacklisted_skipped` and adds a small "Blacklist Write Normalization" requirement.

- **Affected code:**
  - `apps/mailing/views.py` — split GET / POST handlers, add `@require_http_methods(["GET", "POST"])` and `@csrf_exempt` (for the one-click POST contract; the unsubscribe token in the URL is the auth factor).
  - `apps/mailing/engine.py` — add `List-Unsubscribe` and `List-Unsubscribe-Post` headers to `_send_via_gmail` (build into the raw RFC 822 MIME before base64url encoding) and to `_send_via_microsoft` (the Microsoft Graph payload accepts an `internetMessageHeaders` array; values must start with `x-` per Graph rules — Microsoft documents `List-Unsubscribe` and `List-Unsubscribe-Post` as the two exceptions allowed without the `x-` prefix in API versions ≥ 1.0; if blocked we fall back to the headers as `x-list-unsubscribe` / `x-list-unsubscribe-post` and accept the slight deliverability haircut on the Microsoft path).
  - `apps/mailing/models.py` — add `MailingLog.unsubscribed_at` (forward migration only).
  - `apps/companies/models.py` — add `Blacklist.add(email, reason)` classmethod that lowercases / strips the email before `get_or_create`.
  - `apps/companies/importers.py` — count rows whose lowercased email is in `Blacklist`; expose `blacklisted_skipped` in the return tuple; pass it through to `CompanyImportBatch` (a new column or stored inside `error_log` JSON).
  - `apps/companies/admin.py` — display `blacklisted_skipped` on the import batch list/detail.
  - `templates/mailing/unsubscribe_confirm.html` — new template with the confirm form.
  - `templates/mailing/unsubscribe.html` — keep, becomes the post-POST success page.
  - `apps/mailing/urls.py` — no path change (same URL, but the view now multi-methods).
  - `apps/mailing/migrations/000X_mailinglog_unsubscribed_at.py` — additive nullable column, no backfill needed.
  - `apps/companies/migrations/000X_…` — only if `CompanyImportBatch` gains a `blacklisted_skipped` column rather than reusing `error_log`.
  - `conftest.py` — add fixtures `blacklisted_company`, `unsubscribed_log`.
  - `apps/mailing/tests/test_views.py`, `apps/mailing/tests/test_engine.py` — new tests above.

- **Migration / ops impact:**
  - One additive migration on `mailing.MailingLog`. Zero downtime; nullable column, no backfill.
  - One optional additive migration on `companies.CompanyImportBatch` if we choose the dedicated column over JSON.
  - No data migration on `Blacklist` — existing rows stay valid.
  - The `templates/mailing/unsubscribe.html` body changes; staff who have memorised the URL behaviour need a heads-up that GET is now a confirm page.

- **Deliverability:**
  - Adding `List-Unsubscribe` headers should *improve* spam scoring at Gmail and Yahoo immediately. No risk of regression.
  - Removing the silent GET-mutation will cause a measurable drop in the rate of fresh `Blacklist` inserts (we expect 30–70 % fewer inserts in the first week, all of which were scanner-induced false positives).

## Audit follow-ups (review feedback, pre-archive)

After sections 1–8 of `tasks.md` were implemented, an end-of-implementation audit surfaced four small spec/code/test divergences and one documentation drift. Section 9 of `tasks.md` tracks the remediation. The substantive changes:

- **Idempotent-POST timestamp semantics locked.** The original "Idempotent POST" scenario in `specs/mailing/spec.md` said `MailingLog.unsubscribed_at is updated to the latest POST time`, but the implementation in `apps/mailing/views.py:104-106` (`if not log.unsubscribed_at:`) preserves the first timestamp and the corresponding test asserts the same. The spec text has been updated to lock first-write-wins; this matches the shipped behavior, requires no code change, and only renames the test (9.1.3) to make the contract self-documenting.
- **Graph fallback WARNING gated to once-per-process.** The "Graph rejects unprefixed header" scenario already required `exactly once per process`, but the implementation emitted the warning on every fallback and lacked a test. Added a module-level sentinel + a back-to-back-send test that proves a single WARNING across N retries (9.2). Spec text now also nails down the `extra` dict shape so analytics dashboards can rely on it.
- **Importer counter dedup'd.** The `blacklisted_skipped` counter incremented per row, so a dirty input with duplicate emails inflated the count without producing more `Company` rows (the unique constraint on `Company.email` collapsed them). The semantics now read "distinct blacklisted emails encountered" with a new scenario covering the duplicate case (9.3).
- **Unsubscribe log hash aligned with `Blacklist.add`.** The structured-log SHA-256 was computed from `email.lower()` while `Blacklist.add` normalizes via `.strip().lower()`. Whitespace in `company_email_snapshot` would cause analytics joins to silently miss. Hash input is now `email.strip().lower()`, with a new scenario and test asserting both sides of the join produce the same digest (9.4).
- **Documentation drift fixed.** All references to `_send_via_outlook` (which was the proposal's working name) have been updated to the actual function name `_send_via_microsoft` (9.5).

These edits are deliberately rolled into the existing change rather than spawned as a separate `fix-*` proposal because (a) `harden-unsubscribe-flow` has not yet archived, so its requirements live in `changes/`, not `specs/` — a follow-up `## MODIFIED` would target a non-existent requirement until archive — and (b) every audit item is a refinement of the original change, not a new initiative.

## Out of scope (deliberately deferred)

- **Per-user opt-out vs global opt-out.** The current "global blacklist by company email" model is correct for the recipient (companies). Splitting opt-outs per FastJob user would require a richer schema and is not required to fix the reported issues.
- **Re-loading the blacklist mid-beat.** `process_mailing_queue` materialises the blacklist once per run. If a recipient unsubscribes during a run, they are still picked up next beat. Acceptable.
- **Materializing the blacklist as a subquery instead of a Python `set`.** Performance is fine well beyond expected blacklist size; revisit if the table crosses ~50k rows.
- **Admin "remove from blacklist" audit trail.** Out of scope; the existing `BlacklistAdmin` row delete is sufficient for now.
