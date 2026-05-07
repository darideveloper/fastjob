# Tasks: Fix Excel-import timeout

## 1. Infrastructure — shared volume
- [x] 1.1 In `docker-compose.yml`, declare a top-level named volume `imports_data` (with a `${COOLIFY_VOLUME_IMPORTS_DATA:-imports_data}` indirection to match the existing pattern used for `postgres_data`).
- [x] 1.2 Mount `imports_data:/app/imports` on the `web` service.
- [x] 1.3 Mount the same volume `imports_data:/app/imports` on the `celery_worker` service.
- [x] 1.4 Document in `README.md` (Deployment section) that any non-Docker deployment MUST provide a shared filesystem path between web and worker for `/app/imports` (or whatever `COMPANY_IMPORT_LOCAL_PATH` resolves to).

## 2. Settings
- [x] 2.1 Add `COMPANY_IMPORT_LOCAL_PATH = config("COMPANY_IMPORT_LOCAL_PATH", default=str(BASE_DIR / "imports"))` to `config/settings.py`.
- [x] 2.2 Add `COMPANY_IMPORT_MAX_FILE_MB = config("COMPANY_IMPORT_MAX_FILE_MB", default=25, cast=int)`.
- [x] 2.3 Add `COMPANY_IMPORT_FILE_RETENTION_DAYS = config("COMPANY_IMPORT_FILE_RETENTION_DAYS", default=7, cast=int)`.
- [x] 2.4 Register `STORAGES["imports"]` with `BACKEND = "django.core.files.storage.FileSystemStorage"` and `OPTIONS = {"location": COMPANY_IMPORT_LOCAL_PATH, "base_url": None}`. Apply the same registration in both branches of the `if STORAGE_AWS:` block so behavior is independent of the S3 toggle.
- [x] 2.5 Add a new management command `apps/companies/management/commands/setup_company_import_periodics.py` that creates / updates a `CrontabSchedule` (`minute=30, hour=3, timezone="Europe/Madrid"`) and a `PeriodicTask` row pointing to `apps.companies.tasks.purge_stale_company_import_files`. Follow the pattern in `apps/mailing/management/commands/setup_periodic_tasks.py` (django-celery-beat `DatabaseScheduler` is configured in `config/settings.py:232`, so periodic tasks live in the DB and are NOT defined via `CELERY_BEAT_SCHEDULE`). Document running the command once after migrations in `README.md`.
- [x] 2.6 Add `COMPANY_IMPORT_LOCAL_PATH` propagation to the `celery_worker` service env in `docker-compose.yml` so it matches the volume mount path.

## 3. Model and storage wiring
- [x] 3.1 In `apps/companies/models.py`, replace `storage=PrivateMediaStorage()` on `CompanyImportBatch.file` with a callable that resolves the named storage at runtime: `from django.core.files.storage import storages; def _imports_storage(): return storages["imports"]` and `storage=_imports_storage`.
- [x] 3.2 Change `upload_to` to the strftime-aware string `"companies/%Y/%m/%d/"` so the local FS does not accumulate thousands of files in a single directory. Django's `FileField` expands strftime patterns in `upload_to` strings natively, which keeps the resulting migration deterministic — using a callable here would force the migration to import-path-serialize the function and break if the function is ever moved or renamed.
- [x] 3.3 Run `python manage.py makemigrations companies`. If a migration is generated (it likely will be, because `upload_to` is migration-tracked), commit it as `0010_alter_companyimportbatch_file.py` — note that storage backends are NOT migration-tracked, so only the `upload_to` change shows up.
- [x] 3.4 Verify there are no other model fields still referencing `PrivateMediaStorage` for import-related files.

## 4. Admin form and view
- [x] 4.1 In `apps/companies/admin.py`, add `clean_xlsx_file` to `XlsxImportForm` that:
  - rejects extensions other than `.xlsx`,
  - rejects files larger than `settings.COMPANY_IMPORT_MAX_FILE_MB * 1024 * 1024` bytes with a localized error message including the cap.
- [x] 4.2 Refactor `CompanyAdmin.import_xlsx_view`:
  - Validate form (returns the form template with errors on bad input).
  - Create the `CompanyImportBatch` row first with `status="PENDING"` and no file.
  - Inside `try/except (OSError, SuspiciousFileOperation)`: call `batch.file.save(name, request.FILES["xlsx_file"], save=True)`.
  - On success: dispatch `process_company_import.delay(batch.id)` and redirect with a success message that links to `/admin/companies/companyimportbatch/<id>/`.
  - On exception: set `batch.status="FAILED"`, append `{"phase": "upload", "error": str(exc)}` to `batch.error_log`, save, and return a 500 with a JSON error body if the request looks like XHR (header `X-Requested-With: XMLHttpRequest` or `Accept: application/json`), else redirect with an error message.
- [x] 4.3 Make the admin view accept `Accept: application/json` and respond with `{"error": "..."}` on 4xx/5xx so the front-end can surface a real message.
- [x] 4.4 Set `X-Requested-With` from the JS upload so the server can branch on it (purely cosmetic — works either way).

## 5. Front-end
- [x] 5.1 In `templates/admin/companies/import_xlsx.html`:
  - Add `xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest")` and `xhr.setRequestHeader("Accept", "application/json")`.
  - On `xhr.load` with bad status: try to parse `xhr.responseText` as JSON and display `data.error || "Error al subir el archivo. Por favor inténtalo de nuevo."`.
- [x] 5.2 Add a visible note on the form indicating the maximum file size (read from the form's help text via Django so the JS does not need to know the value).

## 6. Celery task lifecycle
- [x] 6.1 In `apps/companies/tasks.py`, replace the `tempfile.NamedTemporaryFile` + `f.read()` pattern with a direct read from `batch.file.path` (FileSystemStorage exposes `.path`) — no copy needed when the file is already local.
- [x] 6.2 On `COMPLETED`, call `batch.file.delete(save=False)`, clear `batch.file.name = ""`, and persist via a single `batch.save(update_fields=[…, "file", …])` (see task 9.5 — `file` MUST be in `update_fields` so the cleared name reaches the DB; the post-audit collapse merges this into the same UPDATE that flips `status` to `COMPLETED`).
- [x] 6.3 On `FAILED`, leave the file in place and append `{"phase": "process", "file_path": batch.file.name}` to `error_log`.
- [x] 6.4 Add a new task `purge_stale_company_import_files()` that:
  - Iterates batches with `created_at < now - COMPANY_IMPORT_FILE_RETENTION_DAYS days` whose `file` is non-empty.
  - Deletes the underlying file via `batch.file.delete(save=False)` and clears the `name` field.
  - Logs a single info line per purge run with counts (deleted / skipped-missing / errored).
- [x] 6.5 Add a `manage.py check_company_import_storage` management command that asserts `COMPANY_IMPORT_LOCAL_PATH` exists, is a directory, and is writable. Wire its result into `/healthz` as a non-fatal warning. *(Implementation: command at `apps/companies/management/commands/check_company_import_storage.py`; healthz integration via `imports_storage_check()` in `config/health.py`, merged into the response `warnings` array alongside `oauth_config_check()`.)*

## 7. Tests
- [x] 7.1 In `apps/companies/tests/test_admin_import_view.py` (new), add cases for:
  - happy path → 302 redirect, batch row created with `PENDING`, file present on local FS, celery task dispatched (use `CELERY_TASK_ALWAYS_EAGER=True` or mock).
  - oversize file → form rejection with localized error, no batch row created, no task dispatched.
  - non-`.xlsx` extension → form rejection.
  - storage failure (mock `FileSystemStorage._save` to raise `OSError`) → batch row exists in `FAILED`, error_log populated, JSON error returned for XHR requests.
- [x] 7.2 In `apps/companies/tests/test_tasks.py`, add cases:
  - successful processing deletes the local file.
  - failed processing leaves the file on disk.
  - `purge_stale_company_import_files` removes only files whose batch's `created_at` exceeds the retention window.
- [x] 7.3 Use `tmp_path` (pytest fixture) and `override_settings(COMPANY_IMPORT_LOCAL_PATH=...)` so tests do not touch real disk paths.
- [x] 7.4 Verify the spec scenarios all map to at least one test in 7.1 / 7.2 (see `specs/companies/spec.md`).

## 9. Post-audit hardening (applied after first implementation pass)
- [x] 9.1 Wire imports-path check into `/healthz`. Add `imports_storage_check()` in `config/health.py` that returns warnings for missing / non-directory / non-writable `COMPANY_IMPORT_LOCAL_PATH`, and merge its output into the `warnings` array of the `healthz()` response. Logs each warning at WARNING level via the same `logger.warning("imports_storage_warning ...")` pattern that `oauth_config_check()` uses.
- [x] 9.2 Replace the double-encoded JSON error body on form-rejection. Previously the admin view returned `{"error": json.dumps({"xlsx_file": [...]})}`, which produced an alert containing serialized JSON. Now returns `{"error": "<first xlsx_file error string>"}` falling back to `"Archivo no válido."` if no error text is present. Drop the now-unused `import json` from `apps/companies/admin.py`.
- [x] 9.3 Tighten `test_oversize_file_rejected_no_batch_created` and `test_non_xlsx_extension_rejected_no_batch_created` to parse the JSON response body and assert on the localized error text (`"demasiado grande"` for the size cap, `".xlsx"` for the extension check). Status-code-only assertions allowed regressions like 9.2 to ship undetected.
- [x] 9.4 Tighten `test_storage_failure_creates_failed_batch_and_returns_json_error` to assert that `error_log` contains a dict whose `phase` key equals `"upload"`, replacing the loose `"upload" in str(entry)` substring check that would have matched any string containing the substring.
- [x] 9.5 Collapse the two-`UPDATE` success path in `process_company_import`. Move `batch.file.delete(save=False)` and `batch.file.name = ""` to *before* the COMPLETED save, so a single `batch.save(update_fields=[...])` records both the cleared file reference and the COMPLETED status atomically.
- [x] 9.6 Wrap the success-path disk delete in `try/except FileNotFoundError`. Prevents an already-cleaned-up file from raising into the celery task and de-syncing `batch.status="COMPLETED"` from the celery task result.
- [x] 9.7 Add a migration-pin comment to `_imports_storage` in `apps/companies/models.py` warning that the callable is referenced by migration `0010_alter_companyimportbatch_file` and renaming requires a follow-up migration.
- [x] 9.8 Add `imports/` to `.gitignore` under the existing "User data (PII)" section, with a comment naming the `COMPANY_IMPORT_LOCAL_PATH` default. Prevents operator-uploaded `.xlsx` files from being accidentally committed during local development.
- [x] 9.9 Document the deliberate non-use of `transaction.atomic` around the `import_xlsx_view` create+save sequence. Wrapping in atomic conflicts with the `Resilient Import Upload Pipeline` requirement that "the view MUST create the `CompanyImportBatch` row in `PENDING` state BEFORE attempting to write the uploaded file" — atomic rollback would erase the row entirely on file-write failure, breaking the audit-trail guarantee. The orphan-PENDING window (worker killed between row INSERT and file save) is bounded by the `purge_stale_company_import_files` retention sweep and is acceptable. See `design.md` Decision 4.

## 8. Validation and rollout
- [ ] 8.1 Run `openspec validate fix-excel-import-timeout --strict` and resolve any reported issues.
- [x] 8.2 Run `pytest apps/companies/tests/` locally; all green.
- [ ] 8.3 Manually verify: upload a small (10 KB) `.xlsx` → row appears in `COMPLETED`. Upload an oversize file → form rejects in browser. Upload a corrupt `.xlsx` → row appears in `FAILED`, file stays on disk, error visible in admin.
- [ ] 8.4 Deploy infra change (volume) ahead of the code change; confirm `manage.py check_company_import_storage` passes on both `web` and `celery_worker`.
- [ ] 8.5 Deploy code change.
- [ ] 8.6 After 7 days in prod, archive this change with `openspec archive fix-excel-import-timeout`.
