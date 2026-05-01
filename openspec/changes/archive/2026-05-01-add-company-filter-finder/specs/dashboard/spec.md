## ADDED Requirements

### Requirement: Search Filters Use DB-Backed Dropdowns
The dashboard "Sector / Área" and "Ubicación" inputs SHALL be searchable dropdowns whose option lists are sourced exclusively from the distinct values of `Company.area` and `Company.location` in the database. Users MUST NOT be able to persist a filter value that is not currently present in the allowed-options whitelist. An empty selection MUST mean "no filter on that field".

#### Scenario: Dropdown options reflect the current database state
- **GIVEN** the `Company` table contains exactly three distinct non-empty `area` values: `"Tecnología"`, `"Diseño"`, `"Marketing"`
- **WHEN** a logged-in user opens the dashboard
- **THEN** the "Sector / Área" dropdown lists exactly those three values (in alphabetical order)

#### Scenario: User cannot persist a free-text value
- **GIVEN** the current allowed-options list for `area` does NOT contain the value `"Pesca"`
- **WHEN** the user submits the filter form with `area_filter=Pesca` (e.g. via a hand-crafted POST)
- **THEN** the server rejects the submission with an error message
- **AND** the user's stored `area_filter` remains unchanged

#### Scenario: Empty selection clears the filter
- **WHEN** the user submits the filter form with `area_filter=` (empty string)
- **THEN** the user's stored `area_filter` is set to the empty string
- **AND** the mailing engine treats the user as having no `area` filter

### Requirement: Live Company-Match Counter on Dashboard
The dashboard SHALL display a live counter, immediately below the filter form, showing the number of companies that match the currently-selected filter values. The counter MUST update whenever either dropdown value changes, MUST display only an integer (no company names, emails, or row data), and MUST source its number from the public count endpoint (so engine and counter cannot drift).

#### Scenario: Counter updates when filters change
- **GIVEN** the dashboard counter currently reads `42` for `area=""` and `location=""`
- **WHEN** the user selects `area="Tecnología"` from the dropdown
- **THEN** the counter re-fetches and displays the new count for `area="Tecnología"` within roughly one debounce window (~250 ms after selection)

#### Scenario: Counter shows an integer only
- **WHEN** the counter renders for any filter combination
- **THEN** the rendered text contains only a non-negative integer
- **AND** no part of the response body or DOM exposes a company name, email, or primary key

#### Scenario: Counter agrees with the mailing engine
- **GIVEN** a user has set `area_filter="Tecnología"` and `location_filter="Madrid"`
- **AND** the dashboard counter reads `0`
- **WHEN** the slow-drip task runs for that user
- **THEN** the engine sends nothing for that user (because the eligible-company queryset is empty by the same matching rules)
