# companies Specification

## Purpose
TBD - created by archiving change add-company-filter-finder. Update Purpose after archive.
## Requirements
### Requirement: Public Filter-Options Endpoint
The system SHALL expose a read-only HTTP endpoint at `GET /api/companies/filter-options/` that returns the distinct, non-empty values currently present in `Company.area` and `Company.location`. The endpoint MUST be reachable without authentication and MUST be rate-limited per client IP. The response payload MUST contain only label strings — never any company-identifying field (email, name, primary key, or any other column). All returned values MUST be in lowercase.

#### Scenario: Anonymous client retrieves option list
- **WHEN** an unauthenticated client sends `GET /api/companies/filter-options/`
- **THEN** the response is `200 OK` with a JSON body `{"areas": [<sorted unique non-empty area strings>], "locations": [<sorted unique non-empty location strings>]}`
- **AND** the response body contains no field other than `areas` and `locations`

#### Scenario: Empty / whitespace values are excluded from the option list
- **GIVEN** a `Company` row with `area = ""` and another with `area = "   "`
- **WHEN** the endpoint is called
- **THEN** neither blank value appears in `areas`

#### Scenario: Values are always returned in lowercase
- **GIVEN** companies linked to areas stored as `"tecnología"` and `"diseño"`
- **WHEN** the endpoint is called
- **THEN** `areas` contains `["diseño", "tecnología"]`
- **AND** all entries are lowercase.

#### Scenario: Per-IP rate limit blocks abuse
- **WHEN** a single client IP sends more than the configured per-hour threshold
- **THEN** subsequent requests within that window receive `429 Too Many Requests`

### Requirement: Public Company-Count Endpoint
The system SHALL expose a read-only HTTP endpoint at `GET /api/companies/count/` that accepts optional `area` and `location` query parameters and returns the integer number of companies matching those filters. The endpoint MUST be reachable without authentication, MUST be rate-limited per client IP, and MUST return only an integer count — never any company name, email, primary key, or any other row-level data. Filter values MUST be validated against the current allowed-options whitelist; any value outside the whitelist MUST cause the request to be rejected with `400 Bad Request`.

#### Scenario: Count with no filters returns total eligible companies
- **WHEN** an unauthenticated client sends `GET /api/companies/count/`
- **THEN** the response is `200 OK` with body `{"count": <total non-blacklisted, not-recently-contacted company count>}`

#### Scenario: Count with valid filters uses exact-match semantics
- **GIVEN** companies with `area = "Tecnología"` and `area = "Tecnología Industrial"`
- **WHEN** the client sends `GET /api/companies/count/?area=Tecnología`
- **THEN** the count includes the first row but NOT the second

#### Scenario: Filter value not in whitelist is rejected
- **GIVEN** the current options list does NOT contain the area `"Bricolaje"`
- **WHEN** the client sends `GET /api/companies/count/?area=Bricolaje`
- **THEN** the response is `400 Bad Request` with body `{"error": "invalid_filter"}`

#### Scenario: Empty parameter means "no filter on that field"
- **WHEN** the client sends `GET /api/companies/count/?area=&location=Madrid`
- **THEN** the count includes all companies with `location` equal to `"Madrid"` regardless of `area`

#### Scenario: Response payload exposes no company-identifying data
- **WHEN** the endpoint is called with any combination of parameters
- **THEN** the JSON response body's keys are exactly `{"count"}` on success or `{"error"}` on validation failure
- **AND** no key referencing a company's email, name, ID, or other row-level field appears

#### Scenario: Per-IP rate limit blocks abuse
- **WHEN** a single client IP sends more than the configured per-hour threshold
- **THEN** subsequent requests within that window receive `429 Too Many Requests`

### Requirement: Shared Company-Match Query Helper
The system SHALL expose a single internal query helper that returns the queryset of companies matching a given `(area, location)` filter pair. Both the public count endpoint AND the mailing engine MUST use this helper, so that the count returned to the user is always equal to the set of companies the engine would consider for that user's next send (excluding per-user state such as cooldown).

#### Scenario: Engine and counter use the same matching rules
- **GIVEN** a user with `area_filter = "Tecnología"` and `location_filter = ""`
- **WHEN** the dashboard fetches the company count for that filter pair
- **AND** the mailing engine subsequently selects a company for that user
- **THEN** the company chosen by the engine is a member of the queryset that produced the count

### Requirement: Cache and Invalidation for Filter Data
The filter-options list and per-filter count results SHALL be cached to avoid redundant `DISTINCT` queries on every request. The cache MUST be invalidated whenever a `Company` row is created, updated, or deleted, so that imports surface immediately on both the dashboard and the landing page.

#### Scenario: Options list is served from cache on repeat reads
- **GIVEN** the filter-options endpoint has been called once in the last 5 minutes
- **WHEN** a second client calls the same endpoint
- **THEN** the response is served from cache (no `DISTINCT` query is issued)

#### Scenario: Importing a new company busts the cache
- **GIVEN** the filter-options cache contains a list that does not include `"Logística"`
- **WHEN** the admin imports a new `Company` row with `area = "Logística"`
- **THEN** the next call to the filter-options endpoint returns a list that includes `"Logística"`

#### Scenario: Bulk import busts the cache exactly once
- **WHEN** an admin imports 500 new `Company` rows in a single import run (regardless of how many internal transactions the importer uses to commit them)
- **THEN** the cache is busted exactly once after the import run completes
- **AND** it is NOT busted once per chunk and NOT busted once per row
- **AND** the bust call site is the celery task that orchestrates the import (so per-chunk transactions in the importer do not over-bust the cache)

### Requirement: Managed Filter Taxonomy
The system MUST use a managed taxonomy for Sectors (Areas) and Locations instead of deriving them from raw company data.
- The `Area` and `Location` entities MUST be manageable via the Django Admin.
- `Company` and `User` filter references MUST use ForeignKeys to these entities.
- The `filter_options` API MUST return values from the managed models.

#### Scenario: Admin creates a new Area
- **GIVEN** an administrator in the Django Admin.
- **WHEN** the admin creates an `Area` named "Cybersecurity".
- **THEN** "Cybersecurity" MUST immediately appear as an option in the Dashboard and Landing filters.

#### Scenario: User filter validation
- **GIVEN** a user attempting to save a filter via the dashboard.
- **WHEN** the user submits an `area_filter` that does not exist in the `Area` table.
- **THEN** the system MUST reject the update and show an error message.

### Requirement: Secure Public Counter API
The company count API MUST remain secure and prevent enumeration of non-taxonomy values.
- The API MUST only accept `area` and `location` values that exist in the managed taxonomy.
- Requests with unknown values MUST return HTTP 400.

#### Scenario: Anonymous count request with valid filters
- **GIVEN** an unauthenticated visitor on the landing page.
- **WHEN** the visitor selects a valid "Madrid" location.
- **THEN** the API MUST return the correct count of companies linked to the "Madrid" `Location` record.

### Requirement: Expanded Company Data
The system SHALL store additional metadata for each company to improve the richness of the database and support future features.
The `Company` model MUST include the following fields:
- `address`: The street address of the company.
- `zip_code`: The postal code.
- `province`: The province (e.g., "madrid", "barcelona").
- `community`: The autonomous community (e.g., "com. madrid", "cataluña").
- `phone`: The primary telephone number.
- `fax`: The fax number.
- `website`: The official website URL or domain.

#### Scenario: Company record stores all new fields
- **GIVEN** a company record with address, zip code, province, community, phone, fax, and website
- **WHEN** the record is saved
- **THEN** all fields are persisted in the database.

### Requirement: Enhanced Spanish XLSX Importer
The system SHALL support importing companies from an Excel file using Spanish headers and specific business logic for Spanish data.
The importer MUST process rows within a background task context and:
1. Map `EMPRESA` to `name`, `ACTIVIDAD` to `area`, `DIRECCION` to `address`, `CP` to `zip_code`, `POBLACION` to `location`, `PROVINCIA` to `province`, `COMUNIDAD` to `community`, `TELEFONO` to `phone`, `FAX` to `fax`, `EMAIL` to `email`, and `WEBSITE` to `website`.
2. Split the `ACTIVIDAD` field by the first colon (`:`) and use only the first part as the `Area` name.
3. Normalize all imported string data to lowercase.
4. Materialise the current `Blacklist` email set once per import call and track a `blacklisted_skipped` counter that records the number of **distinct** blacklisted emails encountered in the file — not raw rows. If the same blacklisted email appears N times in the file (e.g. dirty exports with duplicates), the counter MUST advance by exactly 1 across those N rows. The `Company` row MUST still be upserted for every row (so that the row exists if the email is later removed from the blacklist), and the count MUST be returned alongside `created` / `updated` / `errors` and persisted on the `CompanyImportBatch` row that drives the import.
5. Process rows in chunks of `COMPANY_IMPORT_CHUNK_SIZE` rows (default 1000), with each chunk wrapped in its own `transaction.atomic()` block. Within a chunk, taxonomy resolution and company writes MUST use bulk operations (`bulk_create(ignore_conflicts=True)` for new rows, `bulk_update` for existing rows) rather than per-row `update_or_create`, so the import scales to files of 100 000+ rows in seconds rather than minutes.
6. Be idempotent on re-run: if the same input file is processed twice, the second run MUST converge to the same final state without creating duplicate `Company` rows. Existing rows (matched by unique `email`) are routed through the bulk-update path; new rows through `bulk_create(ignore_conflicts=True)`.
7. Skip rows where every cell is empty (typically trailing blanks left by Excel) before advancing the row counter.
8. Tolerate per-row data errors (invalid email, missing required field, etc.) without aborting the chunk: bad rows are appended to the cumulative `errors` list, and the rest of the chunk is committed normally.

#### Scenario: Importer splits ACTIVIDAD and lowercases data
- **GIVEN** an Excel row with `EMPRESA = "KIKO MILANO"`, `ACTIVIDAD = "COSMETICOS: ESTABLECIMIENTOS"`, and `POBLACION = "TORREVIEJA"`
- **WHEN** the file is imported
- **THEN** a `Company` is created with name `"kiko milano"`
- **AND** it is linked to an `Area` named `"cosmeticos"`
- **AND** it is linked to a `Location` named `"torrevieja"`.

#### Scenario: Lowercase invariant survives the bulk-write path
- **GIVEN** an Excel row with `EMAIL = "Contact@KIKO.es"`, `EMPRESA = "KIKO MILANO"`, `WEBSITE = "Https://Kiko.ES"`
- **WHEN** the importer processes the chunk via `bulk_create` (new row) or `bulk_update` (existing row)
- **THEN** the resulting `Company.email` is `"contact@kiko.es"`
- **AND** `Company.name` is `"kiko milano"`
- **AND** `Company.website` is `"https://kiko.es"`
- **AND** the `LowercaseFieldsMixin.save()` hook is NOT relied upon — the importer itself MUST normalize these fields, since `bulk_create` and `bulk_update` bypass `Model.save()` and therefore bypass the mixin
- **AND** re-running the same file produces identical lowercased values (no double-cased rows from a missed normalization in the bulk-update path)

#### Scenario: Importer counts blacklisted rows without dropping them

- **GIVEN** a `Blacklist` row exists for `"contact@kiko.es"`
- **AND** the import file contains a row with `EMAIL = "Contact@kiko.es"`
- **WHEN** the import runs
- **THEN** the returned `blacklisted_skipped` is `1`
- **AND** the `Company` row for `"contact@kiko.es"` is still created or updated
- **AND** the `CompanyImportBatch` record persists `blacklisted_skipped = 1`

#### Scenario: Duplicate blacklisted email in the input is counted once

- **GIVEN** a `Blacklist` row exists for `"contact@kiko.es"`
- **AND** the import file contains three rows whose `EMAIL` column lowercases to `"contact@kiko.es"` (e.g. `"contact@kiko.es"`, `"Contact@KIKO.es"`, `"  contact@kiko.es  "`)
- **WHEN** the import runs
- **THEN** the returned `blacklisted_skipped` is `1`, not `3`
- **AND** exactly one `Company` row exists for `"contact@kiko.es"` (the upsert collapses duplicates by unique email)
- **AND** the `CompanyImportBatch` record persists `blacklisted_skipped = 1`

#### Scenario: Admin sees the blacklisted-skipped count after import
- **GIVEN** an `CompanyImportBatch` with `blacklisted_skipped = 5`
- **WHEN** an administrator opens the batch's admin detail page
- **THEN** the displayed batch summary includes `blacklisted_skipped = 5`

#### Scenario: Re-running a partially-imported file is idempotent
- **GIVEN** a previous import run that committed N chunks before failing partway, leaving M `Company` rows in the database
- **WHEN** an administrator uploads the same file again
- **THEN** the second run completes successfully
- **AND** the total `Company` row count for the emails in the file equals the number of unique emails in the file (no duplicates)
- **AND** rows already imported by the first run are routed through the bulk-update path; rows missed by the first run are routed through the bulk-create path

#### Scenario: One bad row does not abort its chunk
- **GIVEN** an import file containing 1000 valid rows and 1 row with an invalid email
- **WHEN** the import runs with `chunk_size = 1000`
- **THEN** all 1000 valid rows in the chunk are committed
- **AND** the invalid row is appended to `errors`
- **AND** `processed_rows` advances by 1001 (or by 1000 if blank-row skipping applies — in either case the loop continues past the bad row)

#### Scenario: Trailing blank rows are not counted as processed
- **GIVEN** an import file with 50 data rows followed by 200 fully-blank rows (a common Excel artefact)
- **WHEN** the import runs
- **THEN** `processed_rows` reaches 50, not 250
- **AND** `total_rows` reflects the same skipped-blank semantics as the importer (so the dashboard percentage hits 100%)

### Requirement: Asynchronous Excel Import Processing
The system SHALL process Excel company imports asynchronously to prevent request timeouts.
- The system MUST define a `CompanyImportBatch` model (or similar) to store the uploaded file and track processing status (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`).
- The admin view for importing Excel files MUST accept the file, create a tracking record, persist the file to a storage backend that does NOT depend on a remote network round-trip during the request, enqueue a background task, and redirect the user immediately with a success message indicating the background process has started.
- The admin view MUST NOT perform a synchronous upload to remote object storage (S3 / DigitalOcean Spaces / equivalent) inside the request handler.
- The admin view MUST guarantee that exactly one `CompanyImportBatch` row is persisted per upload attempt — including attempts where the file write fails — so administrators can audit every attempt from `/admin/companies/companyimportbatch/`.
- The admin upload view MUST surface diagnostic errors when batch creation or file persistence fails for ANY reason (including but not limited to `OSError`, `SuspiciousFileOperation`, and `django.db.utils.DatabaseError` — e.g. schema drift from an unapplied migration). For XHR requests, the response body MUST be a JSON object whose `error` field names the underlying exception class (e.g. `"ProgrammingError"`) and the exception's message text. The generic fallback string "Error al subir el archivo. Por favor inténtalo de nuevo." MUST NOT be the operator's only signal: the diagnostic message MUST take precedence over the XHR client's fallback. The view MUST log the full traceback server-side via `logger.exception(...)` so Sentry / log aggregation captures it.
- The background task MUST update the status AND the in-flight progress fields (`processed_rows`, `created_count`, `updated_count`, `blacklisted_skipped`, `error_log`) of the tracking record continuously as it progresses, so administrators can observe progress live without waiting for the import to finish. Counters MUST be visible to other database connections (i.e. committed, not held in an open transaction) within `COMPANY_IMPORT_CHUNK_SIZE` rows of being computed.
- The background task MUST record the final counts of created/updated records and any errors encountered when the batch reaches a terminal status.

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
- **AND** `processed_rows` equals `total_rows`
- **AND** the underlying uploaded file is removed from local storage

#### Scenario: Import task encounters a processing error
- **GIVEN** a `CompanyImportBatch` in `PROCESSING` state
- **WHEN** the background worker encounters an unrecoverable error (e.g. invalid file format)
- **THEN** the batch status changes to `FAILED`
- **AND** the error details are recorded on the batch record
- **AND** the underlying uploaded file is retained on local storage so the operator can inspect or re-run it
- **AND** any progress counters already committed by previously-successful chunks remain on the record (they MUST NOT be reset to zero)

#### Scenario: Admin view never blocks on remote storage
- **GIVEN** the configured object-storage endpoint is unreachable
- **WHEN** an administrator submits a valid Excel upload
- **THEN** the admin view still returns a redirect within seconds (no remote PUT is attempted in the request thread)
- **AND** a `CompanyImportBatch` row is created
- **AND** the background task either completes successfully or transitions the batch to `FAILED` — but the request itself does not time out

#### Scenario: In-flight progress is visible to other connections
- **GIVEN** a `CompanyImportBatch` is currently being processed by the background worker
- **WHEN** an administrator queries the batch row (via the admin or via the progress endpoint) at any point during processing
- **THEN** the response reflects all counters committed up to and including the most recently completed chunk
- **AND** the response is observable across separate database connections (i.e. the worker has committed, not merely buffered, the counter writes)

#### Scenario: Schema drift on upload surfaces a diagnostic error
- **GIVEN** the `CompanyImportBatch` model defines a column (e.g. `total_rows`) that does not yet exist in the database (an unapplied migration)
- **WHEN** an administrator submits a valid xlsx upload via XHR to the import view
- **THEN** the admin view catches the underlying `django.db.utils.ProgrammingError`, logs the full traceback server-side, and returns a `500` JSON response whose `error` field contains both the exception class name (`"ProgrammingError"`) and its message text (e.g. `column "total_rows" does not exist`)
- **AND** the response is NOT the generic fallback string "Error al subir el archivo. Por favor inténtalo de nuevo." that the upload XHR uses when no diagnostic JSON is available
- **AND** if a `CompanyImportBatch` row was created before the failure, it is transitioned to `FAILED` with the exception details on `error_log`, preserving the spec's "exactly one batch row per upload attempt" guarantee

### Requirement: Blacklist Write Normalization

All writes to the `Blacklist` table MUST go through a single helper, `Blacklist.add(email, reason="unsubscribe")`. The helper MUST lowercase and strip the email before performing `get_or_create`, so that the lookup phase of `get_or_create` is consistent with the lowercased value the `LowercaseFieldsMixin` writes on `save()`. The helper MUST raise `ValueError` on empty input.

#### Scenario: Mixed-case email normalized on insert

- **WHEN** `Blacklist.add("Foo@Empresa.ES")` is called for the first time
- **THEN** exactly one row is created with `email == "foo@empresa.es"` and `reason == "unsubscribe"`

#### Scenario: Repeat call is idempotent

- **GIVEN** a `Blacklist` row already exists for `"foo@empresa.es"`
- **WHEN** `Blacklist.add("FOO@empresa.es")` is called
- **THEN** no new row is created
- **AND** no `IntegrityError` is raised

#### Scenario: Empty email raises

- **WHEN** `Blacklist.add("")` or `Blacklist.add(None)` is called
- **THEN** the helper raises `ValueError`
- **AND** no row is created

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

### Requirement: Chunked Import Progress Tracking
The system SHALL track in-flight progress of company imports on the `CompanyImportBatch` row so administrators can observe the running import without waiting for completion.
- The `CompanyImportBatch` model MUST have `total_rows` and `processed_rows` integer fields, both defaulting to `0`.
- Before the row-processing loop begins, the celery task MUST set `total_rows` to the count of data rows in the file (excluding the header row), clamped to a defensive ceiling (`5_000_000`) to absorb pathological xlsx files with phantom formatting that report `max_row = 1_048_576`. When the worksheet's `<dimension>` element is missing (`ws.max_row is None`) or appears to be a placeholder (`<= 1`), the preflight MUST stream-count the rows via `iter_rows` after first calling `ws.reset_dimensions()` to clear openpyxl's internal upper bound — without the reset, `iter_rows` would honor the bogus bound and the count would also be wrong. `total_rows` MUST NOT be left at `0` simply because the dimension element was unreliable.
- After every chunk commit, the importer MUST update `processed_rows`, `created_count`, `updated_count`, `blacklisted_skipped`, and `error_log` to reflect the cumulative state including that chunk.
- The progress fields MUST be modified via `Model.save(update_fields=[...])` so unrelated fields (notably `file`, `status`) are not accidentally overwritten by the progress writes.
- On a `FAILED` terminal transition, progress fields MUST NOT be reset; they retain whatever the last committed chunk wrote so administrators can see how far the import got.

#### Scenario: Total rows is set before the row loop starts
- **GIVEN** a 100-row import file (header + 100 data rows)
- **WHEN** `process_company_import` runs
- **THEN** `batch.total_rows` is `100` before the importer's first chunk commit
- **AND** the value is observable to other database connections (the task MUST commit the preflight save)

#### Scenario: Processed rows ticks up as chunks commit
- **GIVEN** an import file of 5 rows and `COMPANY_IMPORT_CHUNK_SIZE = 2`
- **WHEN** the import runs
- **THEN** after the first chunk commits, `processed_rows` is `2`
- **AND** after the second chunk commits, `processed_rows` is `4`
- **AND** after the final chunk commits, `processed_rows` is `5`
- **AND** at every observation point, the four counter fields (`created_count`, `updated_count`, `blacklisted_skipped`, `error_log` length) reflect the cumulative state through the most recently committed chunk

#### Scenario: Pathological max_row is clamped
- **GIVEN** an xlsx file whose `ws.max_row` reports `1_048_576` due to phantom whole-column formatting, but which actually contains 50 data rows
- **WHEN** the preflight runs
- **THEN** `batch.total_rows` is set to a value clamped to at most `5_000_000` (the defensive ceiling)
- **AND** the importer's blank-row skipping ensures `processed_rows` reaches `50` (not `1_048_576`)
- **AND** the dashboard percentage reaches 100% on completion (the importer's final write of `processed_rows = total_rows = 50` corrects the preflight estimate)

#### Scenario: max_row reports None (missing dimension element)
- **GIVEN** an xlsx file with N data rows (plus a header) written by a non-Excel tool that omits the `<dimension>` element, so `ws.max_row` returns `None` in `read_only=True` mode
- **WHEN** the preflight runs
- **THEN** `batch.total_rows` is set to N (recovered via stream-counting through `iter_rows`)
- **AND** it is NOT coerced to `0` (the live progress widget gets a real denominator from the first poll)
- **AND** no `TypeError` is raised by the arithmetic on the absent value

#### Scenario: max_row reports a placeholder bound (<= 1)
- **GIVEN** an xlsx file with N data rows written by a producer that emits a placeholder dimension element (e.g. `<dimension ref="A1:B1"/>` despite N >> 1)
- **WHEN** the preflight runs
- **THEN** the preflight detects the unreliable bound, calls `ws.reset_dimensions()` to clear openpyxl's internal `_max_row` cap, and stream-counts via `iter_rows`
- **AND** `batch.total_rows` is set to N — NOT to `0` and NOT to the placeholder value `1`
- **AND** the live progress widget shows a real denominator from the first poll

#### Scenario: Failed transition preserves progress
- **GIVEN** an import that successfully committed 30 chunks before raising on chunk 31
- **WHEN** the celery task transitions the batch to `FAILED`
- **THEN** `processed_rows`, `created_count`, `updated_count`, and `blacklisted_skipped` remain at the values written by chunk 30
- **AND** the `error_log` entries written by chunks 1-30 are preserved
- **AND** the final entries appended by the task name the failure phase (`"phase": "process"`)

### Requirement: Live Progress Dashboard for Import Batches
The Django admin SHALL surface live, polling-based progress for in-flight `CompanyImportBatch` rows so administrators can monitor running imports without manually refreshing the page.
- The admin MUST expose `GET /admin/companies/companyimportbatch/<int:object_id>/progress/` returning a JSON body with the keys `status`, `total_rows`, `processed_rows`, `created_count`, `updated_count`, `blacklisted_skipped`, `error_count`. `error_count` is the length of `error_log`.
- The endpoint MUST require admin authentication (decorated by `self.admin_site.admin_view(...)` or equivalent). Anonymous access MUST redirect to the admin login.
- The endpoint MUST return `404` for a nonexistent batch ID.
- The change-form template for `CompanyImportBatch` MUST include a progress widget (progress bar + counter widgets) for batches whose status is `PENDING` or `PROCESSING`. The widget MUST be hidden (or not rendered at all) for `COMPLETED` / `FAILED` batches so the standard admin view is the only thing visible after the import is done.
- Inline JavaScript MUST poll the progress endpoint every 2 000 ms while the displayed batch is in a non-terminal state, update the widget in place, and stop polling on terminal status. On a terminal status response, the page MUST be reloaded once so the standard admin re-renders all fields (including the now-cleared file field on `COMPLETED` and the `error_log` on `FAILED`).
- The polling implementation MUST use `setTimeout` (not `setInterval`) to avoid stacking calls if a tick is slower than the interval.

#### Scenario: Operator opens a PROCESSING batch's change page
- **GIVEN** a `CompanyImportBatch` with `status = "PROCESSING"`, `total_rows = 1000`, `processed_rows = 250`
- **WHEN** an administrator opens `/admin/companies/companyimportbatch/<id>/change/`
- **THEN** the rendered HTML includes a progress widget showing `250 / 1000 (25%)`
- **AND** the inline JS starts polling `/admin/companies/companyimportbatch/<id>/progress/` every 2 s
- **AND** as the worker commits more chunks, the progress widget updates without manual refresh

#### Scenario: Polling stops on terminal status
- **GIVEN** an open admin page polling a `PROCESSING` batch
- **WHEN** the worker transitions the batch to `COMPLETED`
- **THEN** the next poll returns `status = "COMPLETED"`
- **AND** the JS stops scheduling further polls
- **AND** the page reloads once so the standard admin view re-renders with the cleared file field and final counters

#### Scenario: Progress endpoint is gated by admin auth
- **GIVEN** the progress endpoint URL `/admin/companies/companyimportbatch/<id>/progress/`
- **WHEN** an unauthenticated client requests it
- **THEN** the response is a `302` redirect to the admin login URL
- **AND** no batch data is leaked in the response body

#### Scenario: Progress endpoint returns 404 for a missing batch
- **WHEN** an authenticated administrator requests the progress endpoint with a batch ID that does not exist
- **THEN** the response is `404 Not Found`

#### Scenario: COMPLETED batches do not show the widget
- **GIVEN** a `CompanyImportBatch` with `status = "COMPLETED"`
- **WHEN** an administrator opens its change page
- **THEN** the progress widget is hidden or not rendered
- **AND** the inline JS does not start polling
- **AND** the page renders the standard admin form (file field, error_log, status flag) only

