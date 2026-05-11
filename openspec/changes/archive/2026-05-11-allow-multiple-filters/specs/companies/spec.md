## MODIFIED Requirements

### Requirement: Shared Company-Match Query Helper
The system SHALL expose a single internal query helper that returns the queryset of companies matching a given set of `(areas, locations)` filters. Both the public count endpoint AND the mailing engine MUST use this helper, so that the count returned to the user is always equal to the set of companies the engine would consider for that user's next send (excluding per-user state such as cooldown). Matching multiple values for the same field MUST use `OR` logic (e.g. `IN`).

#### Scenario: Engine and counter use the same matching rules
- **GIVEN** a user with `area_filters=["Tecnología"]` and `location_filters=[]`
- **WHEN** the dashboard fetches the company count for those filters
- **AND** the mailing engine subsequently selects a company for that user
- **THEN** the company chosen by the engine is a member of the queryset that produced the count

### Requirement: Managed Filter Taxonomy
The system MUST use a managed taxonomy for Sectors (Areas) and Locations instead of deriving them from raw company data.
- The `Area` and `Location` entities MUST be manageable via the Django Admin.
- `Company` filter references MUST use ForeignKeys to these entities.
- `User` filter references MUST use ManyToManyFields to these entities.
- The `filter_options` API MUST return values from the managed models.

#### Scenario: User filter validation
- **GIVEN** a user attempting to save a filter via the dashboard.
- **WHEN** the user submits an `area` value that does not exist in the `Area` table.
- **THEN** the system MUST reject the update and show an error message.
