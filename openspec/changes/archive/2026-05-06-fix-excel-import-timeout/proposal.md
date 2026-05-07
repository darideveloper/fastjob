# Change: Fix Excel-import timeout caused by in-request remote storage upload

## Why
The Excel import view at `/admin/companies/company/import-xlsx/` currently fails: after the browser finishes uploading, the page shows "Guardando en el servidor, por favor espera…" for several minutes and then errors with "Error al subir el archivo." No `CompanyImportBatch` row is ever created, so administrators cannot see what went wrong from `/admin/companies/companyimportbatch/`.

Root cause: `apps/companies/admin.py:67` calls `CompanyImportBatch.objects.create(file=request.FILES["xlsx_file"])`, and the model's `file` field is wired to `PrivateMediaStorage()` (DigitalOcean Spaces). This makes the request thread synchronously PUT the upload to a remote S3 endpoint *before* the row is INSERTed and *before* the Celery task is enqueued. The user-reported "few minutes" before the alert fires lines up with the gunicorn `--timeout 300` setting in `docker-compose.yml:38`: the request is held open for the full Spaces upload, the worker is killed at 300 s, the upstream returns 502/504, the JS sees a bad status and shows "Error al subir el archivo", and because `objects.create()` raised it never reached the SQL INSERT — so no `CompanyImportBatch` row exists. This violates the existing `Asynchronous Excel Import Processing` requirement, which mandates an immediate redirect after enqueueing the task. Secondary failure modes (boto3 retry behavior on a misconfigured endpoint, slow link saturation) are discussed in `design.md` as alternatives to verify in logs.

## What Changes
- **Drop remote object storage from the import-upload critical path.** `CompanyImportBatch.file` will use a new `imports` named storage backed by `FileSystemStorage` instead of `PrivateMediaStorage`.
- **Narrow the existing `Private Storage Backend` infrastructure requirement** so it covers only end-user-uploaded PII (CVs and any future user-submitted documents) and explicitly excludes operator-uploaded company-import `.xlsx` files. The current wording names "Company Excel" but the threat model behind that requirement is PII protection — operator imports contain only the same business contact data that `/api/companies/count/` already exposes at aggregate level, and the file exists transiently for the duration of one import run. The privacy guarantee for CVs is preserved unchanged.
- **Add a shared Docker volume** (`imports_data`) mounted at `/app/imports` in both the `web` and `celery_worker` services so the worker can read what the web container wrote.
- **Re-order the admin view** to (1) create the `CompanyImportBatch` row in `PENDING` state with no file, (2) attach and persist the local file, (3) dispatch the Celery task, (4) redirect. If step 2 fails, the row is updated to `FAILED` with an `error_log` entry and a message is surfaced via `django.contrib.messages` — the admin always sees the attempt.
- **Move file cleanup into the Celery task lifecycle.** On `COMPLETED`, the local file is deleted; on `FAILED`, it is retained for operator inspection.
- **Add a retention sweep.** A new Celery Beat job (`purge_stale_company_import_files`) deletes import files older than `COMPANY_IMPORT_FILE_RETENTION_DAYS` (default 7) regardless of batch status, to bound disk usage.
- **Cap upload size at the form layer** at `COMPANY_IMPORT_MAX_FILE_MB` (default 25) so dirty uploads are rejected before bytes hit the worker.
- **Improve front-end error reporting**: `templates/admin/companies/import_xlsx.html` will read a JSON error body when the server returns a 4xx/5xx and display the server message instead of the generic "Error al subir el archivo."
- **BREAKING (operational, not API)**: deployments must add the `imports_data` volume and (in non-Docker deploys) provision a shared filesystem path. A dedicated `## Migration Plan` is included in `design.md`.

## Impact
- Affected specs:
  - `companies` — modify `Asynchronous Excel Import Processing`; add `Resilient Import Upload Pipeline`, `Import File Lifecycle and Retention`, `Import Upload Size Limit`.
  - `infrastructure` — modify `Private Storage Backend` (narrow scope to user PII); add `Shared Imports Volume Between Web and Worker`.
- Affected code:
  - `apps/companies/admin.py` — view re-ordering and error-surfacing
  - `apps/companies/models.py` — switch `file` field to the named `imports` storage
  - `apps/companies/tasks.py` — read from local path, delete on success, add `purge_stale_company_import_files`
  - `apps/companies/migrations/` — no schema change required (storage is not migration-tracked) but a `0010_alter_companyimportbatch_file.py` may be generated for the `upload_to` rename; verify with `makemigrations`
  - `config/settings.py` — add `STORAGES["imports"]`, `COMPANY_IMPORT_FILE_RETENTION_DAYS`, `COMPANY_IMPORT_MAX_FILE_MB`, register the beat schedule
  - `templates/admin/companies/import_xlsx.html` — surface server error JSON
  - `docker-compose.yml` — declare and mount `imports_data` volume on `web` and `celery_worker`
  - `apps/companies/tests/test_tasks.py`, new `test_admin_import_view.py` — coverage for the new flow
