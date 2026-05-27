## 1. Backend: available-filters query function

- [x] 1.1 Add `get_available_filters(areas=None, locations=None)` to `apps/companies/queries.py` that returns `{"areas": [...], "locations": [...]}` constrained by cross-dimensional filtering. When no filters are selected, fall back to `get_filter_options()`.
- [x] 1.2 Implement cross-dimensional logic: `available_areas` filtered by selected locations, `available_locations` filtered by selected areas. Within the same dimension, OR logic applies (using `__in`).
- [x] 1.3 Add caching with the same version-based pattern as `get_company_count()` — cache key includes sorted inputs and version, TTL of 60 seconds.
- [x] 1.4 Ensure `bust_filter_caches()` already invalidates available-filters caches (it bumps `COUNT_VERSION_KEY`, which is used in the cache key).

## 2. Backend: available-filters API endpoint

- [x] 2.1 Add `available_filters_view` to `apps/companies/views.py` accepting `GET /api/companies/available-filters/?area=X&area=Y&location=Z`.
- [x] 2.2 Validate all `area` and `location` parameters against the managed taxonomy whitelist (same pattern as `companies_count_view`). Return 400 with `{"error": "invalid_filter"}` for unknown values.
- [x] 2.3 Add rate limiting using the same `RATELIMIT_FILTER_COUNT` setting (aligned with the count endpoint).
- [x] 2.4 Add `Cache-Control: public, max-age=60` response header (aligned with count endpoint).
- [x] 2.5 Add URL route in `apps/companies/urls.py`.

## 3. Backend: tests

- [x] 3.1 Add tests for `get_available_filters()` in `apps/companies/tests/test_queries.py`: no filters returns all options, area filter constrains locations, location filter constrains areas, both filters constrain both dimensions, empty result cascade.
- [x] 3.2 Add tests for `available_filters_view` in `apps/companies/tests/test_views.py`: valid parameters, invalid parameters return 400, no parameters returns all options, rate limiting, caching headers.

## 4. Frontend: dynamic combobox options

- [x] 4.1 Add `AVAILABLE_URL = '/api/companies/available-filters/'` constant to `combobox.js`.
- [x] 4.2 Refactor `initCombobox` so the `options` array is mutable and can be updated from outside the closure. Expose an `updateOptions(newOptions)` method on each combobox container element.
- [x] 4.3 Create `scheduleAvailableFilters(widget)` function that fetches available options with the same 250ms debounce as `scheduleCount`. On success, call `updateOptions()` on both comboboxes in the widget.
- [x] 4.4 Integrate `scheduleAvailableFilters` into the `onChange` callback so every selection change triggers both a count update and an available-filters update.
- [x] 4.5 In `updateOptions`, merge currently-selected values into the new options list so pills for selected-but-unavailable values remain removable. The `showDropdown` function must display selected values even if they are not in the available options.
- [x] 4.6 Ensure the dropdown correctly shows available options for the current filter state, excluding already-selected values from the dropdown list (they appear as pills instead).

## 5. Frontend: search-suggestion integration

- [x] 5.1 Update `search-suggestion.js` to rebuild the suggestion pool whenever `FastJobFilter` updates the available options, so suggestions only reference currently-valid area-location combinations.

## 6. Frontend: error handling

- [x] 6.1 Handle available-filters fetch failure gracefully: if the request fails, keep the previous option lists (do not empty the dropdowns). The count request is independent and should still fire.
- [x] 6.2 Handle the case where the available-filters response returns empty lists for a dimension (all combinations yield 0 results): the counter shows 0, and the dropdowns show no selectable options, but already-selected pills remain removable.