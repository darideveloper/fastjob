## ADDED Requirements

### Requirement: Cascading Filter Options API
The system SHALL expose a public API endpoint `GET /api/companies/available-filters/` that returns only the filter options (areas and locations) that yield at least one matching `Company` when combined with the currently-selected filters from the other dimension.

The endpoint MUST accept multi-valued `area` and `location` query parameters (same format as `/api/companies/count/`). It MUST validate all parameter values against the managed taxonomy whitelist and return `400 {"error": "invalid_filter"}` for unknown values. The response MUST be `{"areas": [...], "locations": [...]}` with lists sorted alphabetically.

Cross-dimensional constraint logic:
- **When only areas are selected**: `available_locations` MUST contain only locations that have at least one company in any of the selected areas. `available_areas` MUST return all areas.
- **When only locations are selected**: `available_areas` MUST contain only areas that have at least one company in any of the selected locations. `available_locations` MUST return all locations.
- **When both areas and locations are selected**: `available_areas` MUST be constrained by the selected locations, and `available_locations` MUST be constrained by the selected areas.
- **When no filters are selected**: The response MUST be identical to `GET /api/companies/filter-options/` (all taxonomy values).

Within the same dimension, multi-valued selections use OR logic (e.g. `area=A1&area=A2` means companies in A1 OR A2).

The endpoint MUST use per-IP rate limiting (aligned with the count endpoint's rate), MUST set `Cache-Control: public, max-age=60`, and MUST use server-side caching with version-based invalidation (aligned with `get_company_count`).

#### Scenario: No filters selected returns all options
- **GIVEN** no `area` or `location` query parameters
- **WHEN** `GET /api/companies/available-filters/` is called
- **THEN** the response is identical to `GET /api/companies/filter-options/`
- **AND** the response includes all areas and all locations from the managed taxonomy

#### Scenario: Area filter constrains available locations
- **GIVEN** the database contains companies with `area="tecnología"` in locations `["madrid", "barcelona"]` and no companies with `area="tecnología"` in `"valencia"`
- **WHEN** `GET /api/companies/available-filters/?area=tecnología` is called
- **THEN** `available_locations` includes `"madrid"` and `"barcelona"` but NOT `"valencia"`
- **AND** `available_areas` includes all areas (no location filter is applied)

#### Scenario: Location filter constrains available areas
- **GIVEN** the database contains companies with `location="madrid"` in areas `["tecnología", "derecho"]` and no companies with `location="madrid"` in `"diseño"`
- **WHEN** `GET /api/companies/available-filters/?location=madrid` is called
- **THEN** `available_areas` includes `"derecho"` and `"tecnología"` but NOT `"diseño"`
- **AND** `available_locations` includes all locations (no area filter is applied)

#### Scenario: Both filters constrain both dimensions
- **GIVEN** the database has the following company distribution:
  - `"tecnología"` in `"madrid"` (5 companies)
  - `"tecnología"` in `"barcelona"` (3 companies)
  - `"derecho"` in `"madrid"` (2 companies)
  - `"diseño"` in `"valencia"` (4 companies)
- **WHEN** `GET /api/companies/available-filters/?area=tecnología&location=madrid` is called
- **THEN** `available_areas` includes `"tecnología"` and `"derecho"` (areas present in Madrid)
- **AND** `available_areas` does NOT include `"diseño"` (no diseñadores in Madrid)
- **AND** `available_locations` includes `"madrid"` and `"barcelona"` (locations with tecnología companies)
- **AND** `available_locations` does NOT include `"valencia"` (no tecnología companies in Valencia)

#### Scenario: Multi-valued area filter uses OR logic for location constraint
- **GIVEN** `area="tecnología"` has companies in `"madrid"` and `"barcelona"`, and `area="diseño"` has companies in `"valencia"` only
- **WHEN** `GET /api/companies/available-filters/?area=tecnología&area=diseño` is called
- **THEN** `available_locations` includes `"madrid"`, `"barcelona"`, and `"valencia"`
- **AND** `available_areas` includes all areas

#### Scenario: Invalid filter value returns 400
- **GIVEN** the managed taxonomy does not contain `"sector_inexistente"`
- **WHEN** `GET /api/companies/available-filters/?area=sector_inexistente` is called
- **THEN** the response is `400 {"error": "invalid_filter"}`
- **AND** the `Cache-Control` header is `no-store`

#### Scenario: Case-insensitive validation
- **GIVEN** the managed taxonomy contains `"tecnología"` (lowercase)
- **WHEN** `GET /api/companies/available-filters/?area=Tecnología` is called
- **THEN** the response is `200 OK` with valid available-filters data
- **AND** the result correctly includes locations where tecnología companies exist

#### Scenario: Response is cached with server-side TTL
- **GIVEN** a request for `GET /api/companies/available-filters/?area=tecnología` that was served from cache
- **WHEN** a second request with the same parameters arrives within the TTL window
- **THEN** the response is served from cache without a new database query

#### Scenario: Cache is invalidated when companies are imported
- **GIVEN** a cached available-filters response for area `"tecnología"`
- **WHEN** a new `Company` import creates companies in a previously-empty area-location combination
- **THEN** `bust_filter_caches()` bumps the version key
- **AND** the next available-filters request returns fresh data reflecting the new companies

### Requirement: Available-Filters Query Helper
The system SHALL expose an internal query helper `get_available_filters(areas=None, locations=None)` in `apps/companies/queries.py` that returns `{"areas": [...], "locations": [...]}` constrained by cross-dimensional filtering.

- When no filters are selected, the function MUST return the full taxonomy by calling `get_filter_options()`.
- When areas are selected, `available_locations` MUST be the distinct locations that have at least one `Company` whose `area` matches any of the selected areas.
- When locations are selected, `available_areas` MUST be the distinct areas that have at least one `Company` whose `location` matches any of the selected locations.
- When both are selected, both dimensions MUST be constrained by the other.
- The function MUST accept model instances (or QuerySets) as well as string lists, consistent with `matching_companies_qs`.
- Results MUST be cached using the same version-based pattern as `get_company_count`, with TTL of 60 seconds and a cache key derived from the sorted filter values and the version counter.

#### Scenario: No filters returns full taxonomy
- **GIVEN** `get_available_filters(areas=None, locations=None)` is called
- **THEN** the result is identical to `get_filter_options()`
- **AND** no additional database query is issued beyond what `get_filter_options()` requires

#### Scenario: Areas constrain locations via JOIN
- **GIVEN** companies exist with `area="tecnología"` in `"madrid"` and `"barcelona"` only
- **WHEN** `get_available_filters(areas=["tecnología"], locations=None)` is called
- **THEN** `result["locations"]` equals `["barcelona", "madrid"]` (sorted alphabetically)
- **AND** `result["areas"]` equals the full taxonomy list

#### Scenario: Model instances are accepted
- **GIVEN** an `Area` model instance with `name="tecnología"`
- **WHEN** `get_available_filters(areas=[area_instance], locations=None)` is called
- **THEN** the function extracts the `.name` attribute and returns correct results
- **AND** no `ProgrammingError` or `TypeError` is raised