# companies Specification

## Purpose
TBD - created by archiving change add-company-filter-finder. Update Purpose after archive.
## Requirements
### Requirement: Public Filter-Options Endpoint

The system SHALL expose a read-only HTTP endpoint at `GET /api/companies/filter-options/` that returns the distinct, non-empty values currently present in `Company.area` and `Company.location`. The endpoint MUST be reachable without authentication and MUST be rate-limited per **real client IP** — the visitor IP resolved per the `infrastructure` capability's `Trusted Reverse-Proxy Client IP Resolution` requirement, NOT the connecting socket address (which behind a reverse proxy is identical for every visitor). The response payload MUST contain only label strings — never any company-identifying field (email, name, primary key, or any other column). All returned values MUST be in lowercase. The response MUST be client-cacheable via a `Cache-Control` header so that browsers and shared caches do not re-fetch the (slow-changing) taxonomy on every page view.

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

#### Scenario: Per-IP rate limit blocks abuse and is keyed on the resolved client IP

- **WHEN** a single real client IP sends more than the configured per-hour threshold
- **THEN** subsequent requests from that IP within that window receive `429 Too Many Requests`
- **AND** two distinct visitors behind the same reverse proxy are counted in separate buckets, so one visitor exhausting the limit does NOT cause `429` for the other

#### Scenario: Response is client-cacheable

- **WHEN** an unauthenticated client sends `GET /api/companies/filter-options/`
- **THEN** the `200 OK` response includes a `Cache-Control` header permitting shared caching for a bounded period
- **AND** a browser or edge cache may serve a repeat request within that period without contacting the origin

### Requirement: Public Company-Count Endpoint

The system SHALL expose a read-only HTTP endpoint at `GET /api/companies/count/` that accepts optional `area` and `location` query parameters and returns the integer number of companies matching those filters. The endpoint MUST be reachable without authentication, MUST be rate-limited per **real client IP** (resolved per the `infrastructure` capability's `Trusted Reverse-Proxy Client IP Resolution` requirement, NOT the connecting socket address), and MUST return only an integer count — never any company name, email, primary key, or any other row-level data. Filter values MUST be validated against the current allowed-options whitelist; any value outside the whitelist MUST cause the request to be rejected with `400 Bad Request`. A successful response MUST be client-cacheable via a `Cache-Control` header; the `400` validation-failure response MUST NOT be cached.

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
- **AND** the `400` response is not stored by browser or shared caches

#### Scenario: Empty parameter means "no filter on that field"

- **WHEN** the client sends `GET /api/companies/count/?area=&location=Madrid`
- **THEN** the count includes all companies with `location` equal to `"Madrid"` regardless of `area`

#### Scenario: Response payload exposes no company-identifying data

- **WHEN** the endpoint is called with any combination of parameters
- **THEN** the JSON response body's keys are exactly `{"count"}` on success or `{"error"}` on validation failure
- **AND** no key referencing a company's email, name, ID, or other row-level field appears

#### Scenario: Per-IP rate limit blocks abuse and is keyed on the resolved client IP

- **WHEN** a single real client IP sends more than the configured per-hour threshold
- **THEN** subsequent requests from that IP within that window receive `429 Too Many Requests`
- **AND** two distinct visitors behind the same reverse proxy are counted in separate buckets

### Requirement: Shared Company-Match Query Helper
The system SHALL expose a single internal query helper that returns the queryset of companies matching a given set of `(areas, locations)` filters. Both the public count endpoint AND the mailing engine MUST use this helper, so that the count returned to the user is always equal to the set of companies the engine would consider for that user's next send (excluding per-user state such as cooldown). Matching multiple values for the same field MUST use `OR` logic (e.g. `IN`).

#### Scenario: Engine and counter use the same matching rules
- **GIVEN** a user with `area_filters=["Tecnología"]` and `location_filters=[]`
- **WHEN** the dashboard fetches the company count for those filters
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
- `Company` filter references MUST use ForeignKeys to these entities.
- `User` filter references MUST use ManyToManyFields to these entities.
- The `filter_options` API MUST return values from the managed models.

#### Scenario: User filter validation
- **GIVEN** a user attempting to save a filter via the dashboard.
- **WHEN** the user submits an `area` value that does not exist in the `Area` table.
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
1. Map `EMPRESA` to `name`, `ACTIVIDAD` to `area`, `DIRECCION` to `address`, `CP` to `zip_code`, **`PROVINCIA` to `location`**, `PROVINCIA` to `province`, `COMUNIDAD` to `community`, `TELEFONO` to `phone`, `FAX` to `fax`, `EMAIL` to `email`, and `WEBSITE` to `website`.
2. Split the `ACTIVIDAD` field by the first colon (`:`) and use only the first part as the `Area` name.
3. Normalize all imported string data to lowercase.
4. Materialise the current `Blacklist` email set once per import call and track a `blacklisted_skipped` counter that records the number of **distinct** blacklisted emails encountered in the file — not raw rows. If the same blacklisted email appears N times in the file (e.g. dirty exports with duplicates), the counter MUST advance by exactly 1 across those N rows. The `Company` row MUST still be upserted for every row (so that the row exists if the email is later removed from the blacklist), and the count MUST be returned alongside `created` / `updated` / `errors` and persisted on the `CompanyImportBatch` row that drives the import.
5. Process rows in chunks of `COMPANY_IMPORT_CHUNK_SIZE` rows (default 1000), with each chunk wrapped in its own `transaction.atomic()` block. Within a chunk, taxonomy resolution and company writes MUST use bulk operations (`bulk_create(ignore_conflicts=True)` for new rows, `bulk_update` for existing rows) rather than per-row `update_or_create`, so the import scales to files of 100 000+ rows in seconds rather than minutes.
6. Be idempotent on re-run: if the same input file is processed twice, the second run MUST converge to the same final state without creating duplicate `Company` rows. Existing rows (matched by unique `email`) are routed through the bulk-update path; new rows through `bulk_create(ignore_conflicts=True)`.
7. Skip rows where every cell is empty (typically trailing blanks left by Excel) before advancing the row counter.
8. Tolerate per-row data errors (invalid email, missing required field, etc.) without aborting the chunk: bad rows are appended to the cumulative `errors` list, and the rest of the chunk is committed normally.

#### Scenario: Importer splits ACTIVIDAD and lowercases data
- **GIVEN** an Excel row with `EMPRESA = "KIKO MILANO"`, `ACTIVIDAD = "COSMETICOS: ESTABLECIMIENTOS"`, `PROVINCIA = "ALICANTE"`, and `POBLACION = "TORREVIEJA"`
- **WHEN** the file is imported
- **THEN** a `Company` is created with name `"kiko milano"`
- **AND** it is linked to an `Area` named `"cosmeticos"`
- **AND** it is linked to a `Location` named **`"alicante"`** (derived from the `PROVINCIA` column).

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

### Requirement: Robust Company Filter Normalization
The `matching_companies_qs` helper MUST robustly handle both string inputs and model instances (or iterables of model instances) for the `area` and `location` filters. If passed model instances, it MUST extract their `.name` attribute before filtering the `Company` queryset.

#### Scenario: Helper accepts single model instances
- **GIVEN** an `Area` model instance with `name="Tecnología"`
- **WHEN** it is passed as the `area` argument to `matching_companies_qs`
- **THEN** the helper extracts the name and correctly filters `Company.objects.filter(area__name__iexact="Tecnología")`
- **AND** no `psycopg2.ProgrammingError` is raised.

#### Scenario: Helper accepts QuerySet of model instances
- **GIVEN** a `QuerySet` of `Area` model instances (e.g., from `user.area_filters.all()`)
- **WHEN** it is passed as the `area` argument
- **THEN** the helper extracts the names into a list and correctly filters using `area__name__in=[...]`

### Requirement: Real-time Company Counter Updates
The company counter MUST update in real-time as filters are added or removed in both the Landing Page and the Dashboard.

#### Scenario: Counter updates on Landing Page
- **GIVEN** a user is on the Landing Page
- **WHEN** they select "abogados" in the Sector filter
- **THEN** the counter MUST change from the total count to the specific count for "abogados".
- **AND** the API request MUST use the correct query parameters (`/api/companies/count/?area=abogados`).

#### Scenario: Case-insensitive API validation
- **GIVEN** the database contains an Area named "Tecnología"
- **WHEN** a client sends a GET request to `/api/companies/count/?area=tecnología` (lowercase)
- **THEN** the API MUST return a success response with the correct count instead of `invalid_filter`.

### Requirement: Spanish verbose names on Area and Location name fields
`Area` and `Location` (`apps/companies/models.py`) SHALL each declare `verbose_name="Nombre"` on their `name` field.

#### Scenario: Area and Location change forms show "Nombre"
- **WHEN** a staff user opens `/admin/companies/area/<id>/change/`
  or `/admin/companies/location/<id>/change/`
- **THEN** the field label reads `"Nombre"` in Spanish

### Requirement: Spanish verbose names on Company fields
`Company` (`apps/companies/models.py`) SHALL declare explicit Spanish `verbose_name` on every field that previously lacked one.

| Field | verbose_name |
|---|---|
| `email` | `"Email"` |
| `name` | `"Nombre"` |
| `area` | `"Sector"` |
| `location` | `"Localidad"` |
| `address` | `"Dirección"` |
| `zip_code` | `"Código postal"` |
| `province` | `"Provincia"` |
| `community` | `"Comunidad"` |
| `phone` | `"Teléfono"` |
| `fax` | `"Fax"` |
| `website` | `"Sitio web"` |
| `last_received_at` | `"Último envío recibido"` |
| `created_at` | `"Creada el"` |

#### Scenario: Company change form shows Spanish field labels
- **WHEN** a staff user opens `/admin/companies/company/<id>/change/`
- **THEN** every field label matches the Spanish string from the table above
- **AND** no English auto-generated label (e.g. "Zip code", "Last received at") is visible

### Requirement: Spanish verbose names on Blacklist fields
All fields of `Blacklist` (`apps/companies/models.py`) SHALL declare an
explicit `verbose_name` in Spanish.

| Field | verbose_name |
|---|---|
| `email` | `"Email"` |
| `added_at` | `"Añadido el"` |
| `reason` | `"Motivo"` |

#### Scenario: Blacklist change form shows Spanish field labels
- **WHEN** a staff user opens `/admin/companies/blacklist/<id>/change/`
- **THEN** each field label matches the Spanish string from the table above

### Requirement: Spanish verbose names on CompanyImportBatch fields
All fields of `CompanyImportBatch` (`apps/companies/models.py`) SHALL
declare an explicit `verbose_name` in Spanish.

| Field | verbose_name |
|---|---|
| `file` | `"Archivo"` |
| `status` | `"Estado"` |
| `upload_uuid` | `"UUID de subida"` |
| `original_filename` | `"Nombre de archivo original"` |
| `total_rows` | `"Total de filas"` |
| `processed_rows` | `"Filas procesadas"` |
| `created_count` | `"Empresas creadas"` |
| `updated_count` | `"Empresas actualizadas"` |
| `blacklisted_skipped` | `"Omitidas (lista negra)"` |
| `error_log` | `"Registro de errores"` |
| `created_at` | `"Creada el"` |
| `updated_at` | `"Actualizada el"` |

#### Scenario: CompanyImportBatch change form shows Spanish field labels
- **WHEN** a staff user opens
  `/admin/companies/companyimportbatch/<id>/change/`
- **THEN** each field label matches the Spanish string from the table above
- **AND** no English auto-generated label (e.g. "Upload uuid",
  "Blacklisted skipped") is visible

### Requirement: Filter API Throttle Configuration and Resilience

The per-IP rate-limit thresholds for `GET /api/companies/filter-options/` and `GET /api/companies/count/` MUST be operator-configurable via environment variables, with defaults high enough that normal human browsing — including multiple users sharing one public IP (corporate or carrier NAT) — is never throttled, while a single client issuing automated, high-volume requests is still blocked.

Because these endpoints are read-only and expose only label strings and integer counts, rate limiting here is abuse-prevention, not a security boundary. A transient failure of the rate-limiter's cache backend MUST NOT cause the endpoints to reject legitimate traffic: the limiter MUST fail open (serve the request) rather than fail closed (block all clients) when it cannot read its counter.

#### Scenario: Thresholds are operator-configurable

- **GIVEN** an operator sets the filter-options and count rate-limit environment variables
- **WHEN** the application starts
- **THEN** the two endpoints enforce the operator-supplied thresholds
- **AND** when the variables are unset, safe high defaults apply and deployment succeeds unchanged

#### Scenario: Cache-backend failure does not throttle everyone

- **GIVEN** the rate-limiter's cache backend cannot return a counter value for a request (e.g. a transient cache outage or counter-key eviction)
- **WHEN** an unauthenticated client calls `GET /api/companies/filter-options/` or `GET /api/companies/count/`
- **THEN** the request is served normally (the limiter fails open)
- **AND** no client receives a `429` solely because the cache backend was unavailable

#### Scenario: A single abusive IP is still throttled

- **GIVEN** the configured thresholds and a healthy cache backend
- **WHEN** one real client IP exceeds its configured per-hour threshold
- **THEN** further requests from that IP within the window receive `429 Too Many Requests`

