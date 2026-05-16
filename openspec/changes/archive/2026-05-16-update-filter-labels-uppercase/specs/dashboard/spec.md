## ADDED Requirements

### Requirement: Filter option labels display in uppercase on Dashboard
The authenticated dashboard filter widgets (Sector/Área and Ubicación) SHALL display all option labels in UPPERCASE — both inside the dropdown list and inside the selected-value pills. The underlying values submitted to the server for persisting user preferences MUST remain unchanged (lowercase, as stored in the database). The visual transformation MUST be achieved via CSS (`text-transform: uppercase`) so that hidden input values, server-side whitelist validation, and the mailing engine matching logic are unaffected.

#### Scenario: Dropdown option labels appear in uppercase on Dashboard
- **GIVEN** the database contains locations `{"madrid", "barcelona"}`
- **WHEN** an authenticated user opens the Ubicación dropdown on the dashboard
- **THEN** the dropdown list renders the labels as `MADRID` and `BARCELONA`
- **AND** the POST request to `/filtros/` still sends the lowercase values `madrid` and `barcelona`

#### Scenario: Selected pill labels appear in uppercase on Dashboard
- **GIVEN** the user has `location_filters = ["madrid"]` saved
- **WHEN** the dashboard page loads and pre-fills the combobox from `data-value`
- **THEN** the pill inside the Ubicación combobox renders `MADRID`
- **AND** the hidden form input value for that selection remains `madrid`

#### Scenario: Backend validation is unaffected by uppercase display
- **GIVEN** the current allowed-options list for `area` contains `"tecnología"` (lowercase)
- **WHEN** the user submits the filter form after selecting the option displayed as `TECNOLOGÍA`
- **THEN** the server accepts the submission (hidden input value is `tecnología`, which matches
  the whitelist)
- **AND** the user's `area_filters` is updated to `["tecnología"]`
