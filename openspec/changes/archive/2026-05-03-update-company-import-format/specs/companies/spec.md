## ADDED Requirements

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
The importer MUST:
1. Map `EMPRESA` to `name`, `ACTIVIDAD` to `area`, `DIRECCION` to `address`, `CP` to `zip_code`, `POBLACION` to `location`, `PROVINCIA` to `province`, `COMUNIDAD` to `community`, `TELEFONO` to `phone`, `FAX` to `fax`, `EMAIL` to `email`, and `WEBSITE` to `website`.
2. Split the `ACTIVIDAD` field by the first colon (`:`) and use only the first part as the `Area` name.
3. Normalize all imported string data to lowercase.

#### Scenario: Importer splits ACTIVIDAD and lowercases data
- **GIVEN** an Excel row with `EMPRESA = "KIKO MILANO"`, `ACTIVIDAD = "COSMETICOS: ESTABLECIMIENTOS"`, and `POBLACION = "TORREVIEJA"`
- **WHEN** the file is imported
- **THEN** a `Company` is created with name `"kiko milano"`
- **AND** it is linked to an `Area` named `"cosmeticos"`
- **AND** it is linked to a `Location` named `"torrevieja"`.

## MODIFIED Requirements

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
