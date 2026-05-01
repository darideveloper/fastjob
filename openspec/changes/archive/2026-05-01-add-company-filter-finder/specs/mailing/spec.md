## ADDED Requirements

### Requirement: Exact-Match Filter Semantics in Mailing Engine
The slow-drip mailing engine SHALL match a user's `area_filter` and `location_filter` against `Company.area` and `Company.location` using case-insensitive **exact** equality, not substring matching. An empty filter value MUST mean "no filter on that field". The engine MUST source its eligible-company queryset from the same shared helper used by the dashboard's live counter, so that the two cannot drift.

#### Scenario: Substring matches no longer leak across categories
- **GIVEN** a user with `area_filter = "Tecnología"`
- **AND** a `Company` with `area = "Tecnología Industrial"` exists in the database
- **WHEN** the slow-drip task runs for that user
- **THEN** the engine does NOT consider that company as a match
- **AND** the engine only considers companies whose `area` is exactly `"Tecnología"` (case-insensitive)

#### Scenario: Case-insensitive exact match still applies
- **GIVEN** a user with `area_filter = "tecnología"` (lowercase)
- **AND** a `Company` with `area = "Tecnología"` (capitalized) exists in the database
- **WHEN** the slow-drip task runs for that user
- **THEN** the engine considers that company as a match

#### Scenario: Empty filter means "no filter"
- **GIVEN** a user with `area_filter = ""` and `location_filter = "Madrid"`
- **WHEN** the slow-drip task runs for that user
- **THEN** the engine considers all non-blacklisted, not-recently-contacted companies whose `location` is exactly `"Madrid"` (case-insensitive), regardless of `area`

#### Scenario: Engine queryset matches the dashboard counter
- **GIVEN** the dashboard counter reads `N` for a user's current filter pair
- **WHEN** the slow-drip task runs for that user
- **THEN** the engine's eligible-company queryset for that user (before per-user cooldown is applied) has size `N`

### Requirement: One-Time Normalization of Existing User Filters
On deployment of the exact-match semantics, a forward-only data migration SHALL normalize every existing user's `area_filter` and `location_filter`. Any value that does not appear (case-insensitively, after stripping whitespace) in the current `Company.area` / `Company.location` distinct set MUST be cleared to the empty string. Values that do appear MUST be preserved unchanged.

#### Scenario: Stale free-text filter is cleared
- **GIVEN** a user has `area_filter = "ghost-sector"` from the previous free-text era
- **AND** no `Company` row has `area` equal (case-insensitively) to `"ghost-sector"`
- **WHEN** the data migration runs
- **THEN** the user's `area_filter` is set to `""`

#### Scenario: Valid filter survives the migration
- **GIVEN** a user has `area_filter = "Tecnología"`
- **AND** at least one `Company` row has `area = "Tecnología"` (case-insensitively)
- **WHEN** the data migration runs
- **THEN** the user's `area_filter` remains `"Tecnología"`

#### Scenario: Migration is forward-only
- **WHEN** the migration's reverse operation is invoked
- **THEN** the operation is a no-op (cleared filters are NOT restored, since the previous behavior also matched zero rows for those values)
