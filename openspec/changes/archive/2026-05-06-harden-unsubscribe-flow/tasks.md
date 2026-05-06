# Tasks: harden-unsubscribe-flow

Ordered, small, verifiable steps. Each task should leave `pytest -q` green before moving on.

## 1. Foundations: model + helper

- [x] 1.1 Add `Blacklist.add(email, reason="unsubscribe")` classmethod in `apps/companies/models.py`. Lowercases / strips, raises on empty, wraps `get_or_create`.
- [x] 1.2 Add a one-shot data migration `apps/companies/migrations/000X_normalize_blacklist_emails.py` that lowercases every existing `Blacklist.email`. Resolve unique-constraint collisions by keeping the row with the earliest `added_at`.
- [x] 1.3 Add nullable `MailingLog.unsubscribed_at = DateTimeField(null=True, blank=True)` in `apps/mailing/models.py` plus migration `apps/mailing/migrations/000X_mailinglog_unsubscribed_at.py`. No backfill.
- [x] 1.4 Unit test in `apps/companies/tests/test_models.py`: `Blacklist.add("Foo@Bar.com")` creates exactly one lowercase row; second call returns `(obj, created=False)`; passing `""` raises.

## 2. View split: GET = confirm, POST = commit

- [x] 2.1 Create `templates/mailing/unsubscribe_confirm.html` with a CSRF-stamped `<form method="post" action="">`, a "Confirmar baja" submit button, and a brief explainer.
- [x] 2.2 Refactor `apps/mailing/views.py::unsubscribe` to dispatch on method:
  - `GET` → 404 on bad token, otherwise render `unsubscribe_confirm.html` with the masked email (`f@b.com → f***@b.com`).
  - `POST` → resolve email via `log.company_email_snapshot or log.company.email`, call `Blacklist.add(email)`, set `log.unsubscribed_at = timezone.now()` and `save(update_fields=["unsubscribed_at"])`, render `unsubscribe.html`.
- [x] 2.3 Apply `@require_http_methods(["GET", "POST"])` and `@csrf_exempt` to the view (with a `# noqa` comment explaining the UUID token is the auth factor).
- [x] 2.4 Keep the existing `@ratelimit(key="ip", rate="10/h", block=True)` decorator — it now guards both GET (cheap) and POST (mutation).
- [x] 2.5 Emit the structured log line on successful POST: `logger.info("unsubscribed", extra={"user_pk": ..., "template_id": ..., "log_pk": ..., "company_email_sha256": ...})`.

## 3. Tests for the view

- [x] 3.1 `apps/mailing/tests/test_views.py::test_unsubscribe_get_does_not_blacklist` — GET on a valid token returns 200 and `Blacklist.objects.count() == 0`.
- [x] 3.2 `test_unsubscribe_post_creates_blacklist_row` — POST inserts the row, sets `unsubscribed_at`, returns 200 with `unsubscribe.html`.
- [x] 3.3 `test_unsubscribe_post_is_idempotent` — second POST does not raise, count stays at 1, `unsubscribed_at` is unchanged on the second call (or is updated — choose and lock the behaviour in the spec scenario).
- [x] 3.4 `test_unsubscribe_post_one_click_without_csrf_token` — POST with no CSRF cookie / token still succeeds (RFC 8058).
- [x] 3.5 `test_unsubscribe_invalid_token_returns_404`.
- [x] 3.6 `test_unsubscribe_rate_limit_blocks_after_threshold` — 11th request from same IP within an hour returns 429.

## 4. CV download blacklist gate

- [x] 4.1 In `apps/mailing/views.py::cv_download`, before the `boto3.client(...)` block, check `Blacklist.objects.filter(email=(log.company_email_snapshot or log.company.email or "").lower()).exists()`. If true, return `render(request, "mailing/cv_revoked.html", status=410)`.
- [x] 4.2 Create `templates/mailing/cv_revoked.html` (concise: "This download has been revoked").
- [x] 4.3 Test `test_cv_download_blocked_after_unsubscribe` — given a `MailingLog` whose company email is in the blacklist, GET on the CV link returns 410 and the response does NOT contain a presigned URL.

## 5. List-Unsubscribe headers in outgoing email

- [x] 5.1 In `apps/mailing/engine.py::_send_via_gmail`, when assembling the raw RFC 822 MIME, append:
  ```
  List-Unsubscribe: <{unsubscribe_url}>
  List-Unsubscribe-Post: List-Unsubscribe=One-Click
  ```
  before the blank line that separates headers from body. Use just the URL form for now (skip `mailto:` until a follow-up provisions an inbox).
- [x] 5.2 In `apps/mailing/engine.py::_send_via_microsoft`, add an `internetMessageHeaders` array to the Graph payload with the same two headers. If Graph returns 400 on the unprefixed name, fall back to `x-list-unsubscribe` / `x-list-unsubscribe-post` and emit a one-time `logger.warning` per process.
- [x] 5.3 Test `test_send_emits_list_unsubscribe_headers_gmail` — mock `_send_via_gmail`'s HTTP call, assert the base64url-decoded MIME contains both headers and the URL matches the log's `unsubscribe_token`.
- [x] 5.4 Test `test_send_emits_list_unsubscribe_headers_outlook` — assert the Graph payload includes `internetMessageHeaders` with both names.

## 6. Importer awareness

- [x] 6.1 Add `blacklisted_skipped IntegerField default=0` to `apps/companies/models.py::CompanyImportBatch` plus a migration.
- [x] 6.2 In `apps/companies/importers.py::import_companies_from_xlsx`:
  - Materialise `blacklisted = set(Blacklist.objects.values_list("email", flat=True))` once per call.
  - Increment `blacklisted_skipped` for each row whose lowercase email is in `blacklisted` (still upsert the `Company` row).
  - Return `(created, updated, errors, blacklisted_skipped)`.
- [x] 6.3 Update `apps/companies/tasks.py` (the Celery task that drives the importer) to write `blacklisted_skipped` onto the `CompanyImportBatch` row.
- [x] 6.4 Surface `blacklisted_skipped` in `apps/companies/admin.py::CompanyImportBatchAdmin.list_display` and `readonly_fields`.
- [x] 6.5 Test `test_importer_counts_blacklisted_rows` — fixture creates two blacklisted emails before import; the returned tuple has `blacklisted_skipped == 2` and the rows are still created.

## 7. Cleanup and docs

- [x] 7.1 Update `docs/architecture.md` (or the equivalent doc) section on "Unsubscribe" to describe the GET / POST split and the One-Click POST contract.
- [x] 7.2 Update `openspec/project.md` Domain Context entry for "Blacklist" only if the wording becomes inaccurate (it currently says "list of emails that have unsubscribed" — still accurate).
- [x] 7.3 Run `openspec validate harden-unsubscribe-flow --strict` and resolve any warnings. (Currently passes: `Change 'harden-unsubscribe-flow' is valid`.)
- [ ] 7.4 After deploy and one full beat cycle: confirm `Blacklist.objects.count()` rate of new inserts has dropped (sanity check that the GET-pre-fetch bug is gone). Capture in deploy notes.

## 8. Archive

- [ ] 8.1 After production deploy, open archival PR per `openspec/AGENTS.md` Stage 3 — move `changes/harden-unsubscribe-flow/` to `changes/archive/YYYY-MM-DD-harden-unsubscribe-flow/`, update `specs/mailing/spec.md` and `specs/companies/spec.md` with the new requirements, and run `openspec validate --strict`.

## 9. Audit follow-ups (review feedback, pre-archive)

These items came out of an end-of-implementation audit of sections 1–8. They tighten the spec where it drifted from the implementation, harden two pieces of behavior the original tests did not exercise, and clean up a documentation reference. Each task is small and isolated; complete in any order, then re-run `pytest -q` and `openspec validate harden-unsubscribe-flow --strict` before archival.

### 9.1 Lock the idempotent-POST timestamp semantics in spec text (DONE in this revision)

- [x] 9.1.1 Update `specs/mailing/spec.md` "Two-Step Unsubscribe Flow" requirement body to state that `unsubscribed_at` is set on the FIRST successful POST and MUST NOT be overwritten on replays. (Spec edit only — implementation already matches.)
- [x] 9.1.2 Replace the "Idempotent POST on an already-blacklisted email" scenario with "Idempotent POST preserves the first opt-out timestamp" so the AND-clause matches the implementation and the existing `test_unsubscribe_post_is_idempotent` test.
- [x] 9.1.3 Rename the test function `test_unsubscribe_post_is_idempotent` → `test_unsubscribe_post_preserves_first_opt_out_timestamp` so the test's name reflects the spec scenario it verifies. Pure rename, no assertion change.

### 9.2 Make the Microsoft Graph fallback warning truly once-per-process

- [x] 9.2.1 In `apps/mailing/engine.py`, introduce a module-level sentinel (`_graph_fallback_warned: bool = False`) and gate the existing `logger.warning(...)` behind `if not _graph_fallback_warned:` followed by `_graph_fallback_warned = True`. The retry POST itself still happens on every fallback — only the WARNING emission is gated.
- [x] 9.2.2 Extend the WARNING `extra` dict to `{"provider": "microsoft", "status": resp.status_code, "fallback": "x-prefix"}` per the updated spec.
- [x] 9.2.3 Added `apps/mailing/tests/test_engine.py::test_graph_fallback_warning_emitted_once_per_process`: two back-to-back sends each take the 400-then-202 fallback (4 POSTs total), and `caplog` captures exactly one WARNING record with `provider="microsoft"`, `status=400`, `fallback="x-prefix"`. Sentinel reset via `monkeypatch.setattr` for test isolation.
- [x] 9.2.4 Added `apps/mailing/tests/test_engine.py::test_graph_fallback_succeeds_after_400`: a single send where the first POST is 400 and the retry is 202, asserting the retry payload's `internetMessageHeaders` use `x-list-unsubscribe` / `x-list-unsubscribe-post` and the function returns without raising.

### 9.3 De-duplicate the importer's `blacklisted_skipped` counter

- [x] 9.3.1 In `apps/companies/importers.py::import_companies_from_xlsx`, added a `seen_blacklisted = set()` and now only increment `blacklisted_skipped` when `email in blacklisted_set and email not in seen_blacklisted` (then `seen_blacklisted.add(email)`). The `update_or_create` call still runs for every input row.
- [x] 9.3.2 Added `apps/companies/tests/test_importers.py::test_importer_counts_distinct_blacklisted_emails`: input file with three rows whose `EMAIL` lowercases to the same blacklisted address (mixed-case + leading/trailing whitespace variants); asserts `blacklisted_skipped == 1`, `created + updated == 3`, and a single `Company` row exists for the address (the unique constraint collapses upserts).
- [x] 9.3.3 Updated the existing `test_importer_counts_blacklisted_rows` docstring to clarify it is verifying the distinct-count semantics.

### 9.4 Align the unsubscribe structured-log hash with `Blacklist.add` normalization

- [x] 9.4.1 In `apps/mailing/views.py::unsubscribe`, changed the hash computation to `hashlib.sha256(email.strip().lower().encode())` so the digest matches what an analytics consumer would compute against `Blacklist.email`. Also added `"outcome": "unsubscribed"` to the `extra` dict (the spec lists `outcome` as a structured field; the prior implementation only put it in the message body, which broke `caplog`-style filters and analytics joins keyed by attribute).
- [x] 9.4.2 Added `apps/mailing/tests/test_views.py::test_unsubscribe_log_hash_matches_canonical_blacklist_key`: `MailingLog` with `company_email_snapshot="  Contact@Empresa.ES  "`, POST the unsubscribe, capture the `outcome="unsubscribed"` record via `caplog`, assert `record.company_email_sha256 == sha256(b"contact@empresa.es").hexdigest()`, and assert the matching `Blacklist.email` row is `"contact@empresa.es"` so both sides of the join are demonstrated.

### 9.5 Documentation cleanup (DONE in this revision)

- [x] 9.5.1 Replace `_send_via_outlook` with `_send_via_microsoft` in `proposal.md`, `design.md`, `tasks.md` (task 5.2), and `specs/mailing/spec.md` (Graph header scenario) so all references match the actual function name in `apps/mailing/engine.py`.

### 9.6 Re-validate

- [x] 9.6.1 Ran `pytest -q apps/mailing apps/companies` — `153 passed`, including the four new tests (one unrelated pre-existing failure in `test_task_user_filter_is_case_insensitive` that also fails on `main` HEAD; tracked separately, out of scope for this audit).
- [x] 9.6.2 Ran `openspec validate harden-unsubscribe-flow --strict` and confirmed `Change 'harden-unsubscribe-flow' is valid`.
