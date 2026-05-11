# companies — spec deltas

## ADDED Requirements

### Requirement: Presigned Upload URL Endpoint
The system SHALL expose an admin-only HTTP endpoint at `POST /admin/companies/company/presign-import-upload/` that, given a file's metadata, returns a short-lived presigned URL the browser can use to upload directly to object storage. The endpoint MUST NOT accept the file body itself — only metadata describing the intended upload.

The request body MUST be JSON with the following fields:
- `filename`: the operator's original file name (string, max 255 chars)
- `content_length`: the file's size in bytes (integer)
- `content_type`: the file's MIME type (string)

The response on success MUST be `200 OK` with a JSON body:
```
{
  "url": "<presigned PUT URL valid for COMPANY_IMPORT_PRESIGN_EXPIRY_SECONDS seconds>",
  "key": "imports/<upload_uuid>/<sanitized_filename>",
  "headers": {"Content-Type": "...", "Content-Length": "..."},
  "expires_in": <seconds>,
  "batch_id": <CompanyImportBatch.id>,
  "upload_uuid": "<uuid4>"
}
```

A `CompanyImportBatch` row MUST be created at presign time, before the URL is returned, with `status = "PENDING"`, `upload_uuid = <generated UUID>`, `original_filename = <raw filename>`, and `file = ""` (empty until the trigger step). This row binds the eventual upload-trigger request back to the same batch.

The endpoint MUST validate `content_length <= COMPANY_IMPORT_MAX_FILE_MB * 1024 * 1024`, MUST validate `filename.lower().endswith(".xlsx")`, MUST validate `content_type` is one of the allowed Excel MIME types, and MUST be gated by `self.admin_site.admin_view(...)` (admin authentication). Validation failures MUST return `400 Bad Request` with `{"error": "<localized human message>"}` and MUST NOT create the `CompanyImportBatch` row.

The endpoint MUST work identically against AWS S3 and DigitalOcean Spaces (and any other S3-API-compatible service) by using `boto3.client("s3", endpoint_url=settings.AWS_S3_ENDPOINT_URL or None, region_name=settings.AWS_S3_REGION_NAME, ...)`. When `AWS_S3_ENDPOINT_URL` is empty, boto3 MUST fall back to AWS S3.

#### Scenario: Admin requests a presigned URL for a valid file
- **GIVEN** an authenticated administrator
- **AND** `COMPANY_IMPORT_MAX_FILE_MB = 100`
- **WHEN** the admin POSTs `{"filename": "companies.xlsx", "content_length": 52428800, "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}`
- **THEN** the response is `200 OK` with a JSON body containing `url`, `key`, `headers`, `expires_in`, `batch_id`, and `upload_uuid`
- **AND** a `CompanyImportBatch` row exists with `status = "PENDING"`, `upload_uuid` matching the response, `original_filename = "companies.xlsx"`, and `file` empty
- **AND** the `url` is parseable and points at the configured `AWS_S3_ENDPOINT_URL` (or AWS S3 if endpoint is unset)

#### Scenario: Oversize file is rejected before presigning
- **GIVEN** `COMPANY_IMPORT_MAX_FILE_MB = 100`
- **WHEN** the admin POSTs `{"filename": "huge.xlsx", "content_length": 209715200, "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}`
- **THEN** the response is `400 Bad Request` with `{"error": "<message naming the 100 MB cap>"}`
- **AND** no `CompanyImportBatch` row is created
- **AND** no presigned URL is returned

#### Scenario: Wrong extension rejected before presigning
- **WHEN** the admin POSTs `{"filename": "companies.csv", ...}`
- **THEN** the response is `400 Bad Request` with an extension error
- **AND** no `CompanyImportBatch` row is created

#### Scenario: Non-admin client is redirected to admin login
- **WHEN** an unauthenticated client POSTs to the presign endpoint
- **THEN** the response is a `302` redirect to the admin login URL
- **AND** no `CompanyImportBatch` row is created
- **AND** no presigned URL is generated

#### Scenario: Filename with non-ASCII characters is sanitised in the object key
- **WHEN** the admin POSTs `{"filename": "Copy of BBDDESPAÑA-575.xlsx", ...}`
- **THEN** the returned `key` matches the regex `^imports/[0-9a-f-]{36}/[A-Za-z0-9_.-]+\.xlsx$`
- **AND** the `key` does NOT contain non-ASCII characters
- **AND** `CompanyImportBatch.original_filename` retains the original `"Copy of BBDDESPAÑA-575.xlsx"` for display

#### Scenario: Endpoint works against DigitalOcean Spaces
- **GIVEN** `AWS_S3_ENDPOINT_URL = "https://nyc3.digitaloceanspaces.com"`
- **WHEN** the admin POSTs a valid presign request
- **THEN** the returned `url` hostname matches `<bucket>.nyc3.digitaloceanspaces.com` (or the path-style equivalent)
- **AND** a real PUT to that URL with the matching headers and body succeeds against DO Spaces

#### Scenario: Endpoint works against AWS S3
- **GIVEN** `AWS_S3_ENDPOINT_URL` is unset (empty)
- **AND** `AWS_S3_REGION_NAME = "eu-west-1"`
- **WHEN** the admin POSTs a valid presign request
- **THEN** the returned `url` hostname matches `<bucket>.s3.eu-west-1.amazonaws.com`
- **AND** a real PUT to that URL with the matching headers and body succeeds against AWS S3

### Requirement: S3-Backed Imports Storage Backend
The system SHALL provide an object-storage-backed implementation of `STORAGES["imports"]` selected when `STORAGE_AWS=True`. The backend MUST be `config.storage_backends.ImportsStorage`, a subclass of `S3Boto3Storage` configured with `default_acl = "private"`, `file_overwrite = False`, `custom_domain = False`, and a `location` of `f"{AWS_PROJECT_FOLDER}/imports"`.

When `STORAGE_AWS = False`, `STORAGES["imports"]` MUST resolve to `FileSystemStorage` against `COMPANY_IMPORT_LOCAL_PATH` (the existing behaviour for local development), so contributors running `manage.py runserver` are not required to provision a real bucket.

The `apps.companies.models._imports_storage()` helper MUST resolve to whichever backend is configured, and view/task/admin code MUST NOT branch on `STORAGE_AWS` directly — they MUST go through this helper.

The Celery task `process_company_import` MUST read the file via streaming (`batch.file.open("rb")` to a `tempfile.NamedTemporaryFile`), not via `batch.file.path` — because `.path` is a `FileSystemStorage`-only attribute and does not exist on `S3Boto3Storage`. The temp file MUST be removed in a `finally` block whether the import succeeds or fails.

#### Scenario: Production storage routes to S3
- **GIVEN** `STORAGE_AWS = True` and `AWS_STORAGE_BUCKET_NAME = "fastjob-prod"`
- **WHEN** the presign endpoint generates a key `imports/<uuid>/file.xlsx`
- **AND** the browser PUTs the file body to the presigned URL
- **AND** the trigger view sets `batch.file.name = key`
- **THEN** `batch.file.storage` is an instance of `ImportsStorage`
- **AND** `batch.file.storage.exists(key)` returns `True`
- **AND** `batch.file.size` returns the uploaded byte count via `HeadObject`

#### Scenario: Local-dev storage stays on the filesystem
- **GIVEN** `STORAGE_AWS = False` and `COMPANY_IMPORT_LOCAL_PATH = "/tmp/imports"`
- **WHEN** the test suite or a developer triggers the import flow
- **THEN** uploaded files land under `/tmp/imports/...` exactly as in the pre-change behaviour
- **AND** no S3 client calls are made

#### Scenario: Celery task streams the file from S3 via a temp file
- **GIVEN** `STORAGE_AWS = True` and a `CompanyImportBatch` whose `file.name` points at an existing S3 object
- **WHEN** `process_company_import(batch_id)` runs
- **THEN** the task downloads the object body to a `tempfile.NamedTemporaryFile` and passes the temp file's path to `_preflight_total_rows` and `load_workbook`
- **AND** the temp file is removed before the task returns (success or exception)
- **AND** no call to `batch.file.path` is made

## MODIFIED Requirements

### Requirement: Resilient Import Upload Pipeline
The admin upload pipeline SHALL persist a `CompanyImportBatch` row for every upload attempt and SHALL surface presign / upload / trigger errors back to the operator without losing the audit trail. The pipeline is now a three-step JSON exchange (presign → direct PUT to object storage → trigger), not a single multipart form submission.

- The presign endpoint MUST create the `CompanyImportBatch` row in `PENDING` state with a generated `upload_uuid`, `original_filename`, and an empty `file` field BEFORE returning the presigned URL.
- The trigger endpoint (`POST /admin/companies/company/import-xlsx/`) MUST accept a JSON body `{"upload_uuid", "key"}` referring to the existing batch row and the just-uploaded object key. It MUST validate the key shape against the regex `^imports/[0-9a-f-]{36}/[A-Za-z0-9_.-]+\.xlsx$` AND verify the embedded UUID equals `upload_uuid`.
- The trigger endpoint MUST call `storage.exists(key)` before dispatching the Celery task. If the object is missing (browser PUT failed silently, expired, etc.), the trigger MUST mark the existing batch row `FAILED` with an `error_log` entry whose `phase` is `"upload"` and respond with `400 Bad Request` JSON `{"error": "<localized message>"}`.
- The trigger endpoint MUST call `storage.size(key)` (which translates to `HeadObject`) and reject the import with `400 Bad Request` if the actual uploaded size exceeds `COMPANY_IMPORT_MAX_FILE_MB * 1024 * 1024`. The batch row MUST be marked `FAILED`.
- The trigger endpoint MUST reject `409 Conflict` if the batch row already has a non-empty `file` field (replay protection — a second trigger of the same `upload_uuid` MUST NOT create a duplicate import).
- The Celery task MUST NOT be dispatched if any of the above validations fail.
- All error responses MUST be JSON `{"error": "<localized human message>"}` so the browser displays a real diagnostic, never the generic "Error al subir el archivo" fallback.

The previous form-rejection invariant (oversize / wrong-extension produces JSON 400 with a string `error` field) MOVES to the presign endpoint (covered by the `Presigned Upload URL Endpoint` requirement). It no longer applies to the trigger endpoint, which never receives a file body.

#### Scenario: Object never arrived at S3 (CORS or network failure)
- **GIVEN** the presign endpoint successfully created a `PENDING` batch with `upload_uuid = U`
- **AND** the browser's PUT to S3 failed silently (CORS misconfig, connection drop, etc.)
- **WHEN** the browser POSTs the trigger with `{"upload_uuid": "U", "key": "imports/U/file.xlsx"}`
- **THEN** the trigger calls `storage.exists("imports/U/file.xlsx")` which returns `False`
- **AND** the batch with `upload_uuid = U` is marked `FAILED` with an `error_log` entry whose `phase = "upload"` and `error_class = "ObjectNotFound"`
- **AND** the response is `400 Bad Request` with body `{"error": "La subida no se completó. Vuelve a intentarlo."}`
- **AND** no Celery task is dispatched

#### Scenario: Object on S3 is larger than the cap (forged Content-Length)
- **GIVEN** `COMPANY_IMPORT_MAX_FILE_MB = 100`
- **AND** a malicious client uploaded 200 MB to a presigned URL whose `Content-Length` was 50 MB
- **WHEN** the trigger view receives `{"upload_uuid", "key"}`
- **THEN** `storage.size(key)` reports 200 MB and the trigger rejects with `400 Bad Request` `{"error": "El archivo subido excede el límite de 100 MB"}`
- **AND** the batch is marked `FAILED`
- **AND** no Celery task is dispatched
- **NOTE** S3 should already have rejected the oversized PUT with `403 SignatureDoesNotMatch` because the signed `Content-Length` was 50 MB; this scenario covers the defense-in-depth case where the bucket's signing policy is somehow misconfigured

#### Scenario: Replay of the same trigger does not create a duplicate import
- **GIVEN** a `CompanyImportBatch` whose `upload_uuid = U` has already been triggered (file is set, Celery task dispatched)
- **WHEN** the browser POSTs the trigger again with the same `{"upload_uuid": "U", "key": "..."}`
- **THEN** the response is `409 Conflict` with body `{"error": "Esta subida ya fue procesada."}`
- **AND** no second Celery task is dispatched
- **AND** the existing batch row is unchanged

#### Scenario: Presign succeeded, browser upload succeeded, trigger succeeds
- **GIVEN** a successful presign + browser PUT
- **WHEN** the browser POSTs the trigger with the matching `upload_uuid` and key
- **THEN** the existing `PENDING` batch is updated with `file.name = <key>`
- **AND** `process_company_import.delay(batch.id)` is invoked
- **AND** the response is `200 OK` with body `{"redirect_url": "/admin/companies/companyimportbatch/<id>/change/"}`

#### Scenario: Storage error on the trigger (transient S3 outage)
- **GIVEN** S3 is temporarily returning `500 InternalError` on `HeadObject`
- **WHEN** the browser POSTs the trigger
- **THEN** the trigger MUST NOT mark the batch FAILED on a transient error (it cannot prove the file is missing); it MUST return `503 Service Unavailable` with body `{"error": "El almacenamiento no está disponible. Vuelve a intentarlo en un momento."}` so the browser retries
- **AND** the batch row stays `PENDING` for a future retry

### Requirement: Import Upload Size Limit
The presign endpoint SHALL reject upload requests that exceed `COMPANY_IMPORT_MAX_FILE_MB` (default raised from 25 MB to 100 MB to reflect the new architecture's tolerance) BEFORE returning a presigned URL.
- The cap MUST be enforced at the presign endpoint based on the client-declared `content_length`. A presign request that violates the cap MUST return `400 Bad Request` JSON.
- The cap MUST be re-enforced at S3 itself by including `ContentLength` as a signed header on the presigned PUT URL. The browser MUST send exactly that byte count; S3 MUST reject mismatches with `403`.
- The cap MUST be enforced again at the trigger endpoint via `HeadObject` on the actual uploaded object, in case the bucket policy is misconfigured.
- The cap MUST be communicated to the operator both as form help-text (or in-page copy) and in any rejection message.

#### Scenario: Oversize presign request is rejected
- **GIVEN** `COMPANY_IMPORT_MAX_FILE_MB = 100`
- **WHEN** the admin's browser requests a presign with `content_length = 200 * 1024 * 1024`
- **THEN** the response is `400 Bad Request` with `{"error": "<message naming 100 MB cap>"}`
- **AND** no `CompanyImportBatch` row is created
- **AND** no presigned URL is generated

#### Scenario: Lying about size is caught at the trigger
- **GIVEN** the browser bypasses the JS and forges a presign request with `content_length = 50 MB`
- **AND** uploads a 200 MB body anyway
- **THEN** S3 rejects the PUT with `403 SignatureDoesNotMatch` (because the signed Content-Length differs)
- **OR**, in the unlikely event S3 accepted it, the trigger view's `HeadObject` size check rejects with `400` and marks the batch `FAILED`

#### Scenario: Cap is reflected in form help-text
- **WHEN** an admin opens the import page
- **THEN** the page copy includes the configured cap (e.g. "Tamaño máximo: 100 MB")

### Requirement: Import File Lifecycle and Retention
Uploaded import files SHALL have a bounded lifetime in object storage tied to batch status and a configurable retention window.
- On `COMPLETED`, the underlying object MUST be deleted from object storage via `storage.delete(key)`. For the S3-backed storage this issues a `DeleteObject`; for the local-dev `FileSystemStorage` it removes the on-disk file (existing behaviour).
- On `FAILED`, the file MUST be retained so an operator can inspect it. The path or key MUST appear in `batch.error_log` so the operator can find it (existing behaviour, now applies equally to local files and S3 keys).
- A periodic Celery Beat task SHALL purge any object whose owning `CompanyImportBatch.created_at` is older than `COMPANY_IMPORT_FILE_RETENTION_DAYS` (default 7 days), regardless of the batch's terminal status, so storage usage is bounded.
- The purge task MUST log a single summary line per run including the count of objects deleted, objects skipped because they were already missing, and objects that errored on deletion.
- The purge task MUST work identically against the S3-backed storage (`STORAGE_AWS=True`) and the local-dev storage (`STORAGE_AWS=False`), with no `STORAGE_AWS`-conditional branches in the task.

#### Scenario: Successful import deletes the S3 object
- **GIVEN** `STORAGE_AWS = True` and a `CompanyImportBatch` whose Celery task has just completed processing
- **WHEN** the task transitions the batch to `COMPLETED`
- **THEN** `storage.delete(batch.file.name)` is called, which issues a `DeleteObject` to S3
- **AND** the object is no longer fetchable via `HeadObject`
- **AND** `batch.file.name` is empty

#### Scenario: Failed import keeps the S3 object
- **GIVEN** `STORAGE_AWS = True` and a `CompanyImportBatch` whose Celery task raised mid-processing
- **WHEN** the task transitions the batch to `FAILED`
- **THEN** the object at `batch.file.name` is still present in S3
- **AND** `batch.error_log` includes the key so the operator can fetch it manually via the storage console or a one-off signed URL

#### Scenario: Retention sweep purges old S3 objects regardless of status
- **GIVEN** `STORAGE_AWS = True` and the retention window is set to 7 days
- **AND** a `FAILED` `CompanyImportBatch` was created 10 days ago with its object still in S3
- **WHEN** `purge_stale_company_import_files` runs
- **THEN** the object is deleted from S3
- **AND** `batch.file.name` is cleared to `""`
- **AND** the run logs one summary line including this deletion

#### Scenario: Retention sweep does NOT delete in-window objects
- **GIVEN** the retention window is set to 7 days
- **AND** a `FAILED` `CompanyImportBatch` was created 2 days ago with its object still in S3
- **WHEN** `purge_stale_company_import_files` runs
- **THEN** the object remains in S3
- **AND** `batch.file.name` is unchanged

#### Scenario: Retention sweep handles already-missing objects gracefully
- **GIVEN** a 10-day-old `CompanyImportBatch` whose object was already deleted out-of-band (e.g. lifecycle policy on the bucket)
- **WHEN** `purge_stale_company_import_files` runs
- **THEN** the task does not raise
- **AND** the run's summary line increments the "skipped because already missing" counter
- **AND** `batch.file.name` is cleared to `""` (consistent with the deletion path)
