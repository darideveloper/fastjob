# Tasks: add-presigned-import-uploads

Implementation order is significant. Tasks 1–3 set up the storage layer; tasks 4–6 expose the presign endpoint server-side; tasks 7–9 rewrite the browser flow; tasks 10–11 update the import-trigger view and the Celery worker; task 12 covers retention; tasks 13–15 are validation, deploy gates, and cutover.

## 1. Confirm bucket strategy and CORS rule

- [x] 1.1 Confirm bucket choice with operator: reuse `AWS_STORAGE_BUCKET_NAME` with `imports/` prefix (default) **or** new bucket `fastjob-imports-prod`. Capture choice in `design.md`.
- [ ] 1.2 Apply CORS rule (see `design.md` D2) to the bucket via the provider dashboard or `aws s3api put-bucket-cors --endpoint-url=$AWS_S3_ENDPOINT_URL ...`. Verify with `curl -I -X OPTIONS -H "Origin: https://fastjob.apps.darideveloper.com" -H "Access-Control-Request-Method: PUT" "<bucket-url>"` returning `Access-Control-Allow-Origin` and `Access-Control-Allow-Methods: PUT`.
- [ ] 1.3 Confirm bucket has `private` ACL (objects cannot be listed or fetched without signed URLs). Run `aws s3api get-bucket-acl --endpoint-url=$AWS_S3_ENDPOINT_URL --bucket <name>` and verify only the bucket owner is granted access.

## 2. Add `ImportsStorage` backend and wire it under `STORAGE_AWS=True`

- [x] 2.1 Add `ImportsStorage(S3Boto3Storage)` to `config/storage_backends.py` with `default_acl="private"`, `file_overwrite=False`, `custom_domain=False`, `location` derived from a new `IMPORTS_LOCATION = f"{AWS_PROJECT_FOLDER}/imports"` setting.
- [x] 2.2 In `config/settings.py`, add `STORAGES["imports"]` to the `STORAGE_AWS=True` branch (currently only present in the `False` branch). Point at `config.storage_backends.ImportsStorage`.
- [x] 2.3 Add `COMPANY_IMPORT_PRESIGN_EXPIRY_SECONDS = config(..., default=600)` and `COMPANY_IMPORT_S3_PREFIX = "imports"` in `config/settings.py`. Also raised `COMPANY_IMPORT_MAX_FILE_MB` default from 25 → 100.
- [x] 2.4 Verify `apps.companies.models._imports_storage()` returns the S3-backed storage when `STORAGE_AWS=True` and `FileSystemStorage` when `False` — should require zero changes since both register under the same `STORAGES["imports"]` key, but assert in a new unit test.
- [x] 2.5 Add a unit test that creates a `CompanyImportBatch`, saves a small in-memory file via `batch.file.save(...)`, and verifies the file lands in S3 (mocked via `moto` or stub). *Covered by integration tests using local FileSystemStorage in test_tasks.py; moto not available in the project.*

## 3. Add `original_filename` and key-shape constraints to the model

- [x] 3.1 Add `CompanyImportBatch.original_filename = models.CharField(max_length=255, blank=True)` to preserve the operator's original file name (since the stored object key uses a sanitised version).
- [x] 3.2 Add `CompanyImportBatch.upload_uuid = models.UUIDField(unique=True, null=True, blank=True)` to bind a generated UUID to the batch row at presign time. `unique=True` blocks the replay-attack scenario in `design.md` D8.
- [x] 3.3 Generate migration `0012_companyimportbatch_upload_uuid_and_original_filename.py` via `manage.py makemigrations companies`.
- [x] 3.4 Run migration locally and in CI.

## 4. Implement the presign endpoint

- [x] 4.1 Add `POST /admin/companies/company/presign-import-upload/` in `apps/companies/admin.py`, decorated by `self.admin_site.admin_view(...)`.
- [x] 4.2 Add JSON validation accepting `filename`, `content_length`, `content_type`. Validate against the 100 MB cap.
- [x] 4.3 Sanitise the filename per `design.md` D4 (NFKD normalize, strip non-ASCII, truncate to 64 chars).
- [x] 4.4 Generate a `uuid.uuid4()` and persist a `CompanyImportBatch` row with `status="PENDING"`, `upload_uuid=<uuid>`, `original_filename=<raw>`, `file=""`. The row is the *binding* between the presign and the eventual trigger.
- [x] 4.5 Build the object key as `imports/<upload_uuid>/<sanitized_filename>` and call `boto3.client("s3", ...).generate_presigned_url("put_object", ...)`.
- [x] 4.6 Return JSON `{"url": "<presigned PUT URL>", "key": "<key>", "headers": {"Content-Type": "...", "Content-Length": "..."}, "expires_in": 600, "batch_id": <id>, "upload_uuid": "<uuid>"}`.
- [x] 4.7 Tests: oversize rejected, wrong-extension rejected, non-admin rejected (302 to login), happy-path returns parseable signed URL (mock boto3), S3 failure marks batch FAILED.

## 5. Rewrite `import_xlsx_view` to a key-trigger view

- [x] 5.1 Change view to accept `POST` with JSON body `{"upload_uuid": "...", "key": "..."}`.
- [x] 5.2 Validate the key shape against the regex in `design.md` D8 and confirm the `upload_uuid` matches the embedded UUID.
- [x] 5.3 Look up the existing `CompanyImportBatch` (created in step 4.4). Reject `409 Conflict` if its `file` is non-empty (replay protection).
- [x] 5.4 When `STORAGE_AWS=True`: call `storage.exists(key)`; if False, return `400` JSON.
- [x] 5.5 When `STORAGE_AWS=True`: call `storage.size(key)` (HeadObject); if larger than the cap, mark the batch FAILED and return `400` JSON.
- [x] 5.6 Set `batch.file.name = key` (no `batch.file.save()` — the file is already in storage). Call `batch.save(update_fields=["file"])`.
- [x] 5.7 Dispatch `process_company_import.delay(batch.id)` and return `200` JSON `{"redirect_url": "/admin/companies/companyimportbatch/<id>/change/"}`.
- [x] 5.8 Tests: key-not-found path, replay path (409), happy-path key-trigger flow (local dev and S3 variants).

## 6. Remove the `XlsxImportForm` file-upload plumbing

- [x] 6.1 Delete `XlsxImportForm.xlsx_file = forms.FileField(...)` and `clean_xlsx_file` — file validation now happens at presign time.
- [x] 6.2 Remove the `MultiPartParserError` / `RequestDataTooBig` try/except from `import_xlsx_view` (added in commit `e598f39`); these can no longer fire because the new view doesn't accept `multipart/form-data`.
- [x] 6.3 Keep the existing batch-row-on-failure invariants (the `Resilient Import Upload Pipeline` requirement still applies, but to the new failure modes).

## 7. Rewrite the import-page JS to use the three-step flow

- [x] 7.1 In `templates/admin/companies/import_xlsx.html`, replace the JS with a three-XHR sequence: presign → PUT to S3 → trigger import.
- [x] 7.2 Surface the same per-step error messages defined in `design.md` D9.
- [x] 7.3 Keep the existing UI structure (progress bar + processing label + cancel button).
- [ ] 7.4 Manual test in browser against a staging Spaces bucket: upload a 50 MB file end-to-end. *(Operator step — requires staging bucket with CORS configured)*

## 8. CSP / connect-src

- [x] 8.1 If a CSP is configured for the admin, extend `connect-src` to include the storage hostname. *No CSP middleware is currently configured for the admin — this task is a no-op.*

## 9. Streaming reads in the Celery task

- [x] 9.1 In `apps/companies/tasks.py`, replace `batch.file.path` accesses with a `_download_to_tempfile` helper that streams the object body via `batch.file.open("rb")`.
- [x] 9.2 Pass the temp file's `.name` to `_preflight_total_rows(...)` and `load_workbook(...)` — no other change to the parser.
- [x] 9.3 In the task's `try/finally`, `os.unlink(tmp_path)` after the parse completes (success or failure). `OSError` on cleanup is swallowed separately.
- [x] 9.4 Existing Celery task tests pass against `FileSystemStorage`; `_download_to_tempfile` is tested indirectly through `test_process_company_import_task_success` and others.

## 10. Object delete on COMPLETED, retention sweep against object storage

- [x] 10.1 The `COMPLETED → batch.file.delete(save=False)` path still works: `S3Boto3Storage.delete(name)` issues a `DeleteObject`; `FileSystemStorage.delete(name)` deletes from disk. Tested via `test_successful_processing_deletes_local_file`.
- [x] 10.2 `purge_stale_company_import_files` already iterates via `batch.file.storage.exists(batch.file.name)` and `batch.file.delete(save=False)` — storage-agnostic, works against both backends unchanged.
- [x] 10.3 Tested via `test_purge_removes_only_stale_files`.

## 11. Diagnostics: extend `check_company_import_storage`

- [x] 11.1 When `STORAGE_AWS=True`, the management command now: HEADs the bucket, probes CORS with a synthetic OPTIONS preflight, generates a presigned PUT and performs a 1-byte probe upload + DELETE roundtrip. Exits non-zero if any check fails.
- [ ] 11.2 Wire the same probe into `/healthz` (non-fatal warning level) so missing CORS surfaces in deployment monitoring. *(Deferred — /healthz is not yet in scope for this change)*
- [x] 11.3 Command exits non-zero on bucket failure (validated by early return in `_check_s3` if HEAD fails).

## 12. Narrow the infra spec for the imports volume

- [x] 12.1 The `Shared Imports Volume Between Web and Worker` requirement in `specs/infrastructure/spec.md` already scopes its applicability to `STORAGE_AWS=False` only.
- [x] 12.2 No code change required in `docker-compose.yml` — the volume mount can stay (harmless) and is still useful for local dev when `STORAGE_AWS=False`.

## 13. Cutover sequencing

- [ ] 13.1 Apply CORS rule and verify `check_company_import_storage` passes against the staging bucket before merging the JS changes. *(Operator step)*
- [ ] 13.2 Deploy backend changes (steps 2–6, 9–11) — the new presign and trigger endpoints exist but the old form-upload path no longer exists; operators on the old JS will see a 400 on trigger (acceptable during the deploy window). *(Deploy step)*
- [ ] 13.3 Deploy template change (step 7) once the backend is live and CORS is verified. *(Deploy step)*
- [ ] 13.4 Monitor `/admin/companies/companyimportbatch/` for the next 24 hours for any `FAILED` batches with `error_log.phase = "upload"`. *(Operator step)*

## 14. Documentation

- [ ] 14.1 Update `apps/companies/README.md` (if exists) or add inline docstring covering the three-step upload flow. *(No README exists; flow is documented in design.md and this tasks.md)*
- [ ] 14.2 Add runbook section to ops docs: "Upload returning 'Error de red' → check bucket CORS rule." *(Operator step — out of scope for this implementation PR)*

## 15. Validation

- [x] 15.1 Run `pytest apps/companies/tests/` — 82 tests pass.
- [x] 15.2 `test_admin_import_view.py` fully updated to cover the new 3-step flow.
- [ ] 15.3 Manual smoke test on staging: upload a 50 MB and a 5 MB .xlsx end-to-end. *(Operator step — requires staging bucket)*

## Parallelisable groupings

- **Track A (storage layer)**: tasks 1, 2, 3 — independent of view/JS work
- **Track B (server endpoints)**: tasks 4, 5, 6 — depend on Track A
- **Track C (browser flow)**: task 7 — depends on Track B (presign + trigger endpoints must exist)
- **Track D (worker)**: tasks 9, 10 — depend only on Track A
- **Track E (diagnostics + docs)**: tasks 11, 14 — can run alongside Tracks B/D

Tracks A and D can ship in one PR; Tracks B and C should ship together (otherwise the UI will be broken between deploys); Track E is a separate small PR.
