## Context

The company-finder filter widgets on both the landing page and the dashboard present two independent dropdowns: Sector and Ubicación. Currently, each dropdown lists **all** values from the managed taxonomy (`Area` / `Location` tables), regardless of what the user has selected in the other dropdown. This means a user can select "Abogados familiares" in Sector and then see "Madrid" in Ubicación, only to discover the count is 0 — there are no family lawyers in Madrid in the database.

With 577K companies, 2,403 areas, and 52 locations, the problem is real: many area-location combinations yield zero results, leading to a frustrating dead-end experience.

## Goals

- After any filter selection change, dynamically update **both** dropdowns' option lists to show only values that yield at least one matching company when combined with the current selection in the other dimension.
- Within the same dimension, multiple selections use OR logic (matching the existing count behavior); across dimensions, AND logic applies.
- Already-selected pills remain visible and removable even if they are no longer in the available options list (so the user can escape dead-end states).
- The counter continues to update via the existing `/api/companies/count/` endpoint.
- Performance should remain fast (cached responses, debounced requests, indexed FK joins).

## Non-Goals

- This change does **not** modify the existing `/api/companies/filter-options/` endpoint or `get_filter_options()`. Those continue to return the full taxonomy on page load.
- This change does **not** modify the mailing engine's `matching_companies_qs` query logic.
- This change does **not** add server-side filter validation or session-based filter persistence beyond what already exists.
- This change does **not** modify the dashboard's `update_filters` POST endpoint or its whitelist validation.

## Decisions

### 1. New endpoint vs. extending the existing count endpoint
**Decision**: Add a new `/api/companies/available-filters/` endpoint that returns `{areas: [...], locations: [...]}`.

**Alternatives considered**:
- Extending `/api/companies/count/` to include available filters in its response: This would bloat the count response and break caching semantics (count is cached per exact filter key; available filters change the response shape).
- Adding available-filters as a query parameter on `/api/companies/filter-options/`: This would change an endpoint that's currently cacheable with `Cache-Control: public, max-age=300` into a dynamic one, defeating the 5-minute client cache.

**Rationale**: A separate endpoint has a clear contract, can be cached independently with its own TTL and key strategy, and doesn't risk breaking existing consumers of `filter-options`.

### 2. Cross-dimensional constraint logic
**Decision**: Each dimension constrains the other, not itself.

- **available_areas** = areas where there exists at least one `Company` matching the selected locations (OR within locations). If no locations are selected, all areas are available.
- **available_locations** = locations where there exists at least one `Company` matching the selected areas (OR within areas). If no areas are selected, all locations are available.

This matches standard faceted-search behavior (Amazon, booking sites, etc.) and preserves the maximum useful selection space.

### 3. Caching strategy
**Decision**: Use the same version-based invalidation pattern as `get_company_count()`.

Cache key: `companies:available-filters:v1:{version}|{sorted_areas}|{sorted_locations}`.
TTL: 60 seconds (aligned with count TTL).
Invalidation: `bust_filter_caches()` bumps the version key, orphaning all available-filters caches alongside count caches.

When no filters are selected, short-circuit to `get_filter_options()` (the existing 5-minute cached full taxonomy).

### 4. Frontend debouncing
**Decision**: Share the same 250ms debounce timer as `scheduleCount()`. When a selection changes, both the count fetch and the available-filters fetch are triggered in the same debounced batch.

### 5. Selected pills remain visible even when not in available options
**Decision**: When the available-filters response arrives, the JS merges the currently-selected values into each dropdown's option list. This ensures the user can always deselect a "dead-end" value. Selected pills that are not in the available options are shown in the dropdown with a distinct visual style or simply kept as removable pills.

## Risks / Trade-offs

- **Cache key explosion**: Each unique combination of (areas, locations) generates a separate cache entry. In practice, the number of unique combinations is bounded by user behavior patterns, not by the cross-product of areas × locations. The version-based invalidation pattern keeps this manageable — when new data is imported, all old cache entries are orphaned at once.
- **Extra network request per selection change**: Each change now triggers 2 requests (count + available-filters) instead of 1. Both are lightweight (a JSON object with string lists / a single integer), debounced at 250ms, and cacheable. The UX benefit of preventing dead-end states outweighs the marginal network cost.
- **Race condition between count and available-filters responses**: Since both are fetched concurrently, the count may momentarily show a non-zero number for a combination that available-filters has already eliminated. This is acceptable because the user hasn't had time to interact with the dropdown in the 250ms window.

## Migration Plan
No database migration required. The change is purely additive (new endpoint, new query function, JS refactoring). Rollback is safe — if the new endpoint is removed, the JS falls back to static option lists (the current behavior).

## Open Questions
- None. The cross-dimensional constraint logic matches standard faceted-search UX, and the implementation path is clear.