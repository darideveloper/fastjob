# add-presigned-import-uploads

## Why

The admin company-import upload (`POST /admin/companies/company/import-xlsx/`) routes the entire `.xlsx` body through gunicorn → Traefik → browser. Files larger than ~25 MB intermittently fail with empty 502 Bad Gateway, opaque 400, or the JS-fallback "Error al subir el archivo" message — not because of a single root cause but because of a stack of brittle layers (gunicorn sync-worker holds, Coolify/Traefik buffering, `DATA_UPLOAD_MAX_MEMORY_SIZE`, healthcheck flapping, container memory). Each layer has been tuned in recent commits, but new failure modes keep surfacing as soon as one is patched. The architecture itself — multi-MB form-data through a Django request — is the problem.

This change moves the file body **out of the Django request path entirely**. The browser uploads the `.xlsx` directly to object storage (DigitalOcean Spaces in production, AWS S3 in development/staging) via a short-lived presigned PUT URL. Django sees only small JSON requests: a presign request and an "import-from-key" trigger. The Celery worker reads the file from object storage. Every infrastructure body-size limit between browser and gunicorn becomes irrelevant.

## What Changes

### Capability: companies

- **MODIFIED** `Resilient Import Upload Pipeline` — the upload form no longer accepts the file body via `multipart/form-data`. The view accepts a JSON `{"key": "imports/<id>/<filename>"}` referencing an already-uploaded S3 object and creates the `CompanyImportBatch` with `batch.file.name = key` against the S3-backed `imports` storage backend. The pre-existing batch-row-on-failure invariant is preserved for the new failure modes (presign failure, key-validation failure).
- **MODIFIED** `Import Upload Size Limit` — the size cap is enforced in two places: (a) the presign endpoint validates the requested `content_length` against the cap before returning a URL, and (b) the storage bucket has a presigned-policy condition (`content-length-range`) so a malicious client cannot upload more than the cap even if it forges a Content-Length header.
- **MODIFIED** `Import File Lifecycle and Retention` — the on-disk `COMPLETED → delete file` semantic is preserved, but executes against object storage (`storage.delete(key)`). The retention sweep (`purge_stale_company_import_files`) iterates the `imports/` prefix in the bucket, not a local directory.
- **ADDED** `Presigned Upload URL Endpoint` — new admin-only endpoint `POST /admin/companies/company/presign-import-upload/` that returns `{"url", "key", "headers", "expires_in"}` for a one-shot presigned PUT.
- **ADDED** `S3-Backed Imports Storage Backend` — the `STORAGES["imports"]` entry resolves to an `S3Boto3Storage` subclass (private ACL, dedicated `imports/` prefix) when `STORAGE_AWS=True`, falling back to `FileSystemStorage` only when `STORAGE_AWS=False` (local dev). The Celery task reads via `batch.file.open()` (streaming) instead of `batch.file.path`.

### Capability: infrastructure

- **MODIFIED** `Shared Imports Volume Between Web and Worker` — the requirement is *narrowed* to "applies only when `STORAGE_AWS=False`." Production deployments with object storage MUST NOT require a shared volume between web and worker; the worker reads from object storage directly.
- **ADDED** `Object-Storage CORS Configuration for Imports` — the imports bucket/space MUST have a CORS rule allowing `PUT`, `HEAD` from the production admin origin, with `ETag` exposed. A configuration check command MUST verify this on deploy.

## Impact

- **Affected specs**: `companies`, `infrastructure`
- **Affected code**:
  - `apps/companies/admin.py` — adds presign endpoint, modifies `import_xlsx_view` to accept JSON-with-key, removes `XlsxImportForm` file-field plumbing
  - `apps/companies/tasks.py` — switch from `batch.file.path` to streaming `batch.file.open()`; update `purge_stale_company_import_files` to iterate object-storage prefix
  - `apps/companies/models.py` — adjust `_imports_storage` to return the S3-backed storage when `STORAGE_AWS=True`
  - `config/settings.py` — `STORAGES["imports"]` is already declared in both `STORAGE_AWS=True` and `STORAGE_AWS=False` branches (both currently `FileSystemStorage`); the `True` branch entry MUST be swapped to point at `config.storage_backends.ImportsStorage`. Add `COMPANY_IMPORT_PRESIGN_EXPIRY_SECONDS`, `COMPANY_IMPORT_S3_PREFIX`
  - `config/storage_backends.py` — add `ImportsStorage(S3Boto3Storage)` (private ACL, `imports/` prefix)
  - `templates/admin/companies/import_xlsx.html` — JS rewritten: 1) POST presign request, 2) PUT file to S3 URL, 3) POST trigger to existing view with key
  - `apps/companies/management/commands/check_company_import_storage.py` — extend to probe presign + CORS on the bucket when `STORAGE_AWS=True`
  - new `apps/companies/forms.py` (or inline) — `ImportTriggerForm` for the JSON `{"key"}` body validation
  - tests under `apps/companies/tests/` — new tests for presign endpoint, key-only import flow, retention against S3

- **Risk surface**:
  - Browser→S3 CORS misconfig (silent failure mode)
  - Bucket public-read leakage (mitigated by `default_acl="private"` and `--no-public-read` on bucket)
  - Object-key spoofing (mitigated by presign signature + prefix scoping)
  - DO Spaces vs AWS S3 dialect differences (signature region, virtual-hosted vs path-style, presign quirks) — surfaced in `design.md`

- **No data migration required**: the existing `CompanyImportBatch.file` `FileField` continues to store an opaque key string; only the underlying storage backend changes. Local-dev batches created against `FileSystemStorage` remain readable in dev; production starts using S3 from the cutover.

- **Rollout**: Single-flag (`STORAGE_AWS`) controls the storage backend, so the change is dev-friendly without disturbing local workflows. Once deployed to production, the CORS rule must be applied to the bucket *before* the new template ships, otherwise uploads silently fail in the browser. Sequencing is captured in `tasks.md`.

## Open Decisions Required from the Operator

The following are flagged in `design.md` and gate validation/implementation. The proposal scaffolds reasonable defaults but each has a tradeoff worth your sign-off:

1. **Bucket strategy**: Reuse the existing `AWS_STORAGE_BUCKET_NAME` (with a dedicated `imports/` prefix) **or** provision a separate bucket (`fastjob-imports-prod` etc.)? Default: **same bucket, separate prefix** — simpler IAM, same CORS cost.
2. **Upload mode**: Single PUT (~5 GB cap, simpler JS) **or** S3 multipart (resumable, ≤5 TB)? Default: **single PUT**, with the cap raised from 25 MB → 100 MB. Multipart can be a follow-up if you outgrow it.
3. **New file-size cap**: With S3 in the path, the `COMPANY_IMPORT_MAX_FILE_MB` is no longer a *gunicorn-survivability* knob — it's purely a "guard against operator typos." Default: **100 MB**. Reasonable upper bound for an .xlsx; rejects accidental drops of 5 GB exports.
4. **Local-dev fallback**: Keep `FileSystemStorage` when `STORAGE_AWS=False` (current default for `manage.py runserver`)? Default: **yes, keep it**, because asking devs to provision a real bucket adds friction. Dev path stays exactly as today.
5. **AWS S3 *and* DO Spaces** simultaneously? Default: **single backend per environment**, configured via `AWS_S3_ENDPOINT_URL` (Spaces in prod, AWS in test). The boto3 client is identical; only the endpoint differs. No multi-cloud complexity introduced.
6. **Object-key naming**: `imports/<batch-uuid>/<sanitized-filename>` (preserves operator-readable name) **or** `imports/<batch-uuid>.xlsx` (drops original name)? Default: **first option**, with non-ASCII chars normalised to ASCII-safe equivalents (`Ñ → N`, etc.) so URL-signing is clean.
7. **Retention window for S3 objects**: Reuse `COMPANY_IMPORT_FILE_RETENTION_DAYS` (default 7d)? Default: **yes, same value**, applied via the existing Celery Beat task — no S3 lifecycle policy required, since the task already runs.
8. **Authentication on presign endpoint**: `self.admin_site.admin_view(...)` (admin-only, current pattern)? Default: **yes, same as the existing import view**. No public-facing import flow exists or is planned.

If you accept all defaults, the proposal is ready to validate and implement as written. If you flip any of the eight, I'll update `design.md` and the spec deltas accordingly before validation.
