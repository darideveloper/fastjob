## MODIFIED Requirements
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

## ADDED Requirements
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
