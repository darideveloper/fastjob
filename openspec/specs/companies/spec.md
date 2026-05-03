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
- **WHEN** an admin imports 500 new `Company` rows in a single transaction
- **THEN** the cache is busted once on transaction commit, not 500 times during the import

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

#### Scenario: Importer splits ACTIVIDAD and lowercases data
- **GIVEN** an Excel row with `EMPRESA = "KIKO MILANO"`, `ACTIVIDAD = "COSMETICOS: ESTABLECIMIENTOS"`, and `POBLACION = "TORREVIEJA"`
- **WHEN** the file is imported
- **THEN** a `Company` is created with name `"kiko milano"`
- **AND** it is linked to an `Area` named `"cosmeticos"`
- **AND** it is linked to a `Location` named `"torrevieja"`.

### Requirement: Asynchronous Excel Import Processing
The system SHALL process Excel company imports asynchronously to prevent request timeouts.
- The system MUST define a `CompanyImportBatch` model (or similar) to store the uploaded file and track processing status (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`).
- The admin view for importing Excel files MUST accept the file, create a tracking record, enqueue a background task, and redirect the user immediately with a success message indicating the background process has started.
- The background task MUST update the status of the tracking record as it progresses and record the final counts of created/updated records or any errors encountered.

#### Scenario: Admin uploads a large Excel file
- **WHEN** an administrator uploads a valid `.xlsx` file via the import view
- **THEN** the system immediately redirects to the change list with a message "Import started in the background"
- **AND** the system creates a `CompanyImportBatch` record in `PENDING` state
- **AND** the file is processed asynchronously by a background worker

#### Scenario: Import task completes successfully
- **GIVEN** a `CompanyImportBatch` in `PROCESSING` state
- **WHEN** the background worker finishes importing all valid rows
- **THEN** the batch status changes to `COMPLETED`
- **AND** the batch record contains the count of created and updated companies

#### Scenario: Import task encounters an error
- **GIVEN** a `CompanyImportBatch` in `PROCESSING` state
- **WHEN** the background worker encounters an unrecoverable error (e.g. invalid file format)
- **THEN** the batch status changes to `FAILED`
- **AND** the error details are recorded on the batch record

