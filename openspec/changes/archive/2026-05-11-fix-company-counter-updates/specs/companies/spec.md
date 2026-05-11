## ADDED Requirements

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