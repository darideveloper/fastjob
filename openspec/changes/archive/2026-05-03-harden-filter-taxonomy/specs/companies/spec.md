## ADDED Requirements

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
