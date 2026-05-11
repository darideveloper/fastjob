## MODIFIED Requirements
### Requirement: Search Filters Use DB-Backed Dropdowns
The dashboard "Sector / Área" and "Ubicación" inputs SHALL be searchable dropdowns whose option lists are sourced exclusively from the distinct values of `Company.area` and `Company.location` in the database. Users MUST NOT be able to persist a filter value that is not currently present in the allowed-options whitelist. An empty selection MUST mean "no filter on that field". The dropdowns MUST support multiple selections.

#### Scenario: User cannot persist a free-text value
- **GIVEN** the current allowed-options list for `area` does NOT contain the value `"Pesca"`
- **WHEN** the user submits the filter form with `area_filter=Pesca` (e.g. via a hand-crafted POST)
- **THEN** the server rejects the submission with an error message
- **AND** the user's stored `area_filters` remains unchanged

#### Scenario: Empty selection clears the filter
- **WHEN** the user submits the filter form with no `area_filter` payload
- **THEN** the user's stored `area_filters` is cleared
- **AND** the mailing engine treats the user as having no `area` filter

### Requirement: Live Company-Match Counter on Dashboard
The dashboard SHALL display a live counter, immediately below the filter form, showing the number of companies that match the currently-selected filter values. The counter MUST update whenever either dropdown value changes, MUST display only an integer (no company names, emails, or row data), and MUST source its number from the public count endpoint (so engine and counter cannot drift).

#### Scenario: Counter agrees with the mailing engine
- **GIVEN** a user has set `area_filters=["Tecnología", "Diseño"]` and `location_filters=["Madrid"]`
- **AND** the dashboard counter reads `0`
- **WHEN** the slow-drip task runs for that user
- **THEN** the engine sends nothing for that user (because the eligible-company queryset is empty by the same matching rules)

### Requirement: Restricted Admin User Filters
The Django Admin for the `User` model MUST restrict filter selections to the managed taxonomy.
- The `area_filters` and `location_filters` fields in `UserAdmin` MUST use `filter_horizontal` widgets.
- Staff users MUST NOT be able to enter free-text values into these fields.

#### Scenario: Staff edits user filters
- **GIVEN** a staff user in the Django Admin editing a User.
- **WHEN** the staff user opens the "FastJob" fieldset.
- **THEN** they MUST see multi-select widget (filter_horizontal) for "Area filters" and "Location filters" populated from the managed taxonomy.
