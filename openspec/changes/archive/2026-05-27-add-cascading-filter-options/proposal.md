# Change: Add cascading filter options

## Why
When a user selects a filter value (e.g. "Abogados familiares" in Sector) and then browses the other filter (e.g. Ubicación), they may choose a location that yields zero matching companies. This creates a frustrating UX where the counter shows 0 but the dropdown still offers invalid combinations. Both the landing page and the dashboard are affected.

## What Changes
- Add a new public API endpoint `GET /api/companies/available-filters/` that returns only the filter options that yield at least one matching company, given the current selection in the other dimension.
- Add a backend query function `get_available_filters(areas, locations)` in `apps/companies/queries.py` that uses cross-dimensional constraints (areas filtered by selected locations; locations filtered by selected areas).
- Modify `combobox.js` to dynamically update both comboboxes' option lists after every selection change, fetching available filters from the new endpoint while preserving already-selected pills.
- Modify `search-suggestion.js` to rebuild its suggestion pool whenever the available options change (so suggestions always reference currently-valid combinations).
- The existing `/api/companies/filter-options/` endpoint and `get_filter_options()` function remain unchanged (they still return the full taxonomy for initial page load).
- No changes to the count endpoint or the mailing query logic.

## Impact
- Affected specs: `companies` (new endpoint + query function), `landing` (dynamic filter UX), `dashboard` (dynamic filter UX)
- Affected code: `apps/companies/views.py`, `apps/companies/queries.py`, `apps/companies/urls.py`, `static/js/combobox.js`, `static/js/search-suggestion.js`
- No breaking changes: the new endpoint is purely additive; existing endpoints and behavior are preserved