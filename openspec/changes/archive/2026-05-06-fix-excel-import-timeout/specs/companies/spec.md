## MODIFIED Requirements
### Requirement: Asynchronous Excel Import Processing
The system SHALL process Excel company imports asynchronously to prevent request timeouts.
- The system MUST define a `CompanyImportBatch` model (or similar) to store the uploaded file and track processing status (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`).
- The admin view for importing Excel files MUST accept the file, create a tracking record, persist the file to a storage backend that does NOT depend on a remote network round-trip during the request, enqueue a background task, and redirect the user immediately with a success message indicating the background process has started.
- The admin view MUST NOT perform a synchronous upload to remote object storage (S3 / DigitalOcean Spaces / equivalent) inside the request handler.
- The admin view MUST guarantee that exactly one `CompanyImportBatch` row is persisted per upload attempt — including attempts where the file write fails — so administrators can audit every attempt from `/admin/companies/companyimportbatch/`.
- The background task MUST update the status of the tracking record as it progresses and record the final counts of created/updated records or any errors encountered.

#### Scenario: Admin uploads a large Excel file
- **WHEN** an administrator uploads a valid `.xlsx` file via the import view
- **THEN** the system immediately redirects to the change list with a success message that names the new batch
- **AND** the system creates a `CompanyImportBatch` record in `PENDING` state with the file persisted to local-filesystem storage
- **AND** the file is processed asynchronously by a background worker

#### Scenario: Import task completes successfully
- **GIVEN** a `CompanyImportBatch` in `PROCESSING` state
- **WHEN** the background worker finishes importing all valid rows
- **THEN** the batch status changes to `COMPLETED`
- **AND** the batch record contains the count of created and updated companies
- **AND** the underlying uploaded file is removed from local storage

#### Scenario: Import task encounters a processing error
- **GIVEN** a `CompanyImportBatch` in `PROCESSING` state
- **WHEN** the background worker encounters an unrecoverable error (e.g. invalid file format)
- **THEN** the batch status changes to `FAILED`
- **AND** the error details are recorded on the batch record
- **AND** the underlying uploaded file is retained on local storage so the operator can inspect or re-run it

#### Scenario: Admin view never blocks on remote storage
- **GIVEN** the configured object-storage endpoint is unreachable
- **WHEN** an administrator submits a valid Excel upload
- **THEN** the admin view still returns a redirect within seconds (no remote PUT is attempted in the request thread)
- **AND** a `CompanyImportBatch` row is created
- **AND** the background task either completes successfully or transitions the batch to `FAILED` — but the request itself does not time out

## ADDED Requirements
### Requirement: Resilient Import Upload Pipeline
The admin upload view SHALL persist a `CompanyImportBatch` row for every upload attempt and SHALL surface storage errors back to the operator without losing the audit trail.
- The view MUST create the `CompanyImportBatch` row in `PENDING` state BEFORE attempting to write the uploaded file to storage.
- If the file write raises (e.g. `OSError`, `SuspiciousFileOperation`, disk full), the view MUST update the existing batch row to `status = "FAILED"` and append a structured entry to `error_log` describing the failure phase (`"upload"`).
- The view MUST respond with a JSON body of the form `{"error": "<localized human message>"}` and an appropriate 4xx/5xx status when the request `Accept` header includes `application/json` or the request includes `X-Requested-With: XMLHttpRequest`. Otherwise it MUST redirect with a `messages.error(...)` flash.
- The Celery task MUST NOT be dispatched if the file write failed.

#### Scenario: Storage write fails after the batch is created
- **GIVEN** the local imports filesystem is full
- **WHEN** an administrator submits a valid Excel upload
- **THEN** a `CompanyImportBatch` row exists with `status = "FAILED"` and an `error_log` entry whose `phase` is `"upload"`
- **AND** no Celery task is dispatched for that batch
- **AND** the response to the XHR upload is a 5xx status with body `{"error": "<message>"}` so the JS displays the actual reason instead of a generic alert

#### Scenario: Storage write succeeds but the worker is unavailable
- **GIVEN** Redis (the Celery broker) is reachable but no worker is running
- **WHEN** an administrator submits a valid Excel upload
- **THEN** the `CompanyImportBatch` row is created in `PENDING` and the file is on disk
- **AND** the view returns a redirect with a success message
- **AND** the batch remains `PENDING` until a worker comes online and picks it up — no in-request error is raised

#### Scenario: Form rejection returns a human-readable JSON error body
- **GIVEN** an XHR upload with `Accept: application/json` (or `X-Requested-With: XMLHttpRequest`)
- **WHEN** the form rejects the upload (oversize, wrong extension, etc.)
- **THEN** the response status is `400` and the body MUST be `{"error": "<localized human message>"}` where the value of `error` is a plain string suitable for direct display via `alert()`
- **AND** the body MUST NOT be a JSON-encoded string of an object (e.g. `{"error": "{\"xlsx_file\": [\"…\"]}"}`), because the client has no way to know it should JSON-parse the value a second time

### Requirement: Import File Lifecycle and Retention
Uploaded import files SHALL have a bounded on-disk lifetime tied to batch status and a configurable retention window.
- On `COMPLETED`, the underlying file MUST be deleted from local storage.
- On `FAILED`, the file MUST be retained for operator inspection.
- A periodic Celery Beat task SHALL purge any local import file whose owning `CompanyImportBatch.created_at` is older than `COMPANY_IMPORT_FILE_RETENTION_DAYS` (default 7 days), regardless of the batch's terminal status, so disk usage is bounded.
- The purge task MUST log a single summary line per run including the count of files deleted, files skipped because they were already missing, and files that errored on deletion.

#### Scenario: Successful import deletes its source file
- **GIVEN** a `CompanyImportBatch` whose Celery task has just completed processing
- **WHEN** the task transitions the batch to `COMPLETED`
- **THEN** the file at `batch.file.path` no longer exists on disk
- **AND** `batch.file.name` is empty

#### Scenario: Failed import keeps its source file
- **GIVEN** a `CompanyImportBatch` whose Celery task raised mid-processing
- **WHEN** the task transitions the batch to `FAILED`
- **THEN** the file at `batch.file.path` still exists on disk
- **AND** `batch.error_log` includes the path so the operator can find it

#### Scenario: Retention sweep purges old files regardless of status
- **GIVEN** the retention window is set to 7 days
- **AND** a `FAILED` `CompanyImportBatch` was created 10 days ago with its file still on disk
- **WHEN** `purge_stale_company_import_files` runs
- **THEN** the file is deleted from disk
- **AND** `batch.file.name` is cleared to `""`

#### Scenario: Retention sweep does NOT delete files within the window
- **GIVEN** the retention window is set to 7 days
- **AND** a `FAILED` `CompanyImportBatch` was created 2 days ago with its file still on disk
- **WHEN** `purge_stale_company_import_files` runs
- **THEN** the file remains on disk

### Requirement: Import Upload Size Limit
The admin import form SHALL reject uploads that exceed `COMPANY_IMPORT_MAX_FILE_MB` (default 25 MB) BEFORE persisting any bytes to storage.
- The cap MUST be enforced at the Django form layer (not just the JS layer) so a malicious or scripted client cannot bypass it.
- The cap MUST be communicated to the operator both as form help-text and in the rejection message.

#### Scenario: Oversize upload is rejected at the form layer
- **GIVEN** `COMPANY_IMPORT_MAX_FILE_MB = 25`
- **WHEN** an administrator submits a 40 MB `.xlsx` file
- **THEN** the form returns an error like `"Archivo demasiado grande (40 MB > 25 MB)"`
- **AND** no `CompanyImportBatch` row is created
- **AND** no file is written to storage

#### Scenario: Non-xlsx upload is rejected at the form layer
- **WHEN** an administrator submits a `.csv` or `.xls` file via the import view
- **THEN** the form returns an extension error
- **AND** no `CompanyImportBatch` row is created
