## ADDED Requirements

### Requirement: Slow-Drip Campaign Engine Matching

The slow-drip mailing engine SHALL match a user's `area_filters` and `location_filters` against `Company.area` and `Company.location` using case-insensitive **exact** equality, not substring matching. An empty list MUST mean "no filter on that field". The engine MUST source its eligible-company queryset from the same shared helper used by the dashboard's live counter, so that the two cannot drift.

#### Scenario: Filter fields determine eligibility via IN clause
- **GIVEN** a user with `area_filters = ["Tecnología", "Marketing"]`
- **WHEN** the slow-drip task runs for that user
- **THEN** only companies whose `area.name` exactly matches (case-insensitively) `"Tecnología"` or `"Marketing"` are considered for sending
