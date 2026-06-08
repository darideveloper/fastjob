## MODIFIED Requirements

### Requirement: Slow-Drip Campaign Engine Matching
The slow-drip mailing engine SHALL match a user's `area_filters`, `location_filters`, and `sub_area_filters` against `Company.area`, `Company.location`, and `Company.sub_area` using case-insensitive **exact** equality. An empty list MUST mean "no filter on that field". The engine MUST source its eligible-company queryset from the same shared helper used by the dashboard's live counter, so that the two cannot drift.

#### Scenario: Filter fields determine eligibility including sub-areas
- **GIVEN** a user with `sub_area_filters = ["productos de limpieza"]`
- **WHEN** the slow-drip task runs for that user
- **THEN** only companies whose `sub_area.name` exactly matches (case-insensitively) `"productos de limpieza"` are considered for sending
