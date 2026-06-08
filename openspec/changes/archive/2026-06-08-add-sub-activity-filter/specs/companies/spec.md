## MODIFIED Requirements

### Requirement: Enhanced Spanish XLSX Importer
The system SHALL support importing companies from an Excel file using Spanish headers and specific business logic for Spanish data.
The importer MUST process rows within a background task context and:
1. Map `EMPRESA` to `name`, `ACTIVIDAD` to `area`, `SUB ACTIVIDAD` to `sub_area`, `DIRECCION` to `address`, `CP` to `zip_code`, `PROVINCIA` to `location`, `PROVINCIA` to `province`, `COMUNIDAD` to `community`, `TELEFONO` to `phone`, `FAX` to `fax`, `EMAIL` to `email`, and `WEBSITE` to `website`.
2. Split the `ACTIVIDAD` field by the first colon (`:`) and use only the first part as the `Area` name.
3. Normalize all imported string data to lowercase.
4. Materialise the current `Blacklist` email set once per import call and track a `blacklisted_skipped` counter that records the number of **distinct** blacklisted emails encountered in the file — not raw rows. If the same blacklisted email appears N times in the file (e.g. dirty exports with duplicates), the counter MUST advance by exactly 1 across those N rows. The `Company` row MUST still be upserted for every row (so that the row exists if the email is later removed from the blacklist), and the count MUST be returned alongside `created` / `updated` / `errors` and persisted on the `CompanyImportBatch` row that drives the import.
5. Process rows in chunks of `COMPANY_IMPORT_CHUNK_SIZE` rows (default 1000), with each chunk wrapped in its own `transaction.atomic()` block. Within a chunk, taxonomy resolution and company writes MUST use bulk operations (`bulk_create(ignore_conflicts=True)` for new rows, `bulk_update` for existing rows) rather than per-row `update_or_create`, so the import scales to files of 100 000+ rows in seconds rather than minutes.
6. Be idempotent on re-run: if the same input file is processed twice, the second run MUST converge to the same final state without creating duplicate `Company` rows. Existing rows (matched by unique `email`) are routed through the bulk-update path; new rows through `bulk_create(ignore_conflicts=True)`.
7. Skip rows where every cell is empty (typically trailing blanks left by Excel) before advancing the row counter.
8. Tolerate per-row data errors (invalid email, missing required field, etc.) without aborting the chunk: bad rows are appended to the cumulative `errors` list, and the rest of the chunk is committed normally.

#### Scenario: Importer splits ACTIVIDAD and maps SUB ACTIVIDAD and lowercases data
- **GIVEN** an Excel row with `EMPRESA = "KIKO MILANO"`, `ACTIVIDAD = "COSMETICOS: ESTABLECIMIENTOS"`, `SUB ACTIVIDAD = "COSMETICA NATURAL"`, `PROVINCIA = "ALICANTE"`, and `POBLACION = "TORREVIEJA"`
- **WHEN** the file is imported
- **THEN** a `Company` is created with name `"kiko milano"`
- **AND** it is linked to an `Area` named `"cosmeticos"`
- **AND** it is linked to a `SubArea` named `"cosmetica natural"`
- **AND** it is linked to a `Location` named `"alicante"` (derived from the `PROVINCIA` column).

### Requirement: Public Filter-Options Endpoint
The system SHALL expose a read-only HTTP endpoint at `GET /api/companies/filter-options/` that returns the distinct, non-empty values currently present in `Company.area`, `Company.sub_area`, and `Company.location`. The endpoint MUST be reachable without authentication and MUST be rate-limited per **real client IP** — the visitor IP resolved per the `infrastructure` capability's `Trusted Reverse-Proxy Client IP Resolution` requirement, NOT the connecting socket address. The response payload MUST contain only label strings — never any company-identifying field (email, name, primary key, or any other column). All returned values MUST be in lowercase. The response MUST be client-cacheable via a `Cache-Control` header.

#### Scenario: Anonymous client retrieves option list with sub-areas
- **WHEN** an unauthenticated client sends `GET /api/companies/filter-options/`
- **THEN** the response is `200 OK` with a JSON body `{"areas": [<sorted unique areas>], "locations": [<sorted unique locations>], "sub_areas": [<sorted unique sub_areas>]}`
- **AND** the response body contains no fields other than `areas`, `locations`, and `sub_areas`

### Requirement: Public Company-Count Endpoint
The system SHALL expose a read-only HTTP endpoint at `GET /api/companies/count/` that accepts optional `area`, `sub_area`, and `location` query parameters and returns the integer number of companies matching those filters. The endpoint MUST be reachable without authentication, MUST be rate-limited per **real client IP**, and MUST return only an integer count. Filter values MUST be validated against the current allowed-options whitelist; any value outside the whitelist MUST cause the request to be rejected with `400 Bad Request`. A successful response MUST be client-cacheable via a `Cache-Control` header.

#### Scenario: Count with valid sub-area filter
- **GIVEN** companies with `area = "Vendedor"`, `sub_area = "Productos de limpieza"`
- **WHEN** the client sends `GET /api/companies/count/?sub_area=Productos de limpieza`
- **THEN** the count includes only matching companies
- **AND** the response returns 200 OK

### Requirement: Shared Company-Match Query Helper
The system SHALL expose a single internal query helper that returns the queryset of companies matching a given set of `(areas, locations, sub_areas)` filters. Both the public count endpoint AND the mailing engine MUST use this helper. Matching multiple values for the same field MUST use `OR` logic (e.g. `IN`).

#### Scenario: Matches companies with sub-area filters
- **GIVEN** a user with `sub_area_filters=["productos de limpieza"]`
- **WHEN** the dashboard fetches the company count
- **THEN** the company chosen by the engine is a member of the queryset that produced the count
