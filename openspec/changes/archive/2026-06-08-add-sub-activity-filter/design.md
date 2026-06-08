## Context

The system has a two-dimensional taxonomy to match job-seeking users to companies: `Area` (broad sector) and `Location` (geography). We need to introduce a third dimension, `SubArea` (sub-activities, e.g. "productos de limpieza" under "Vendedor"), so users can filter their target companies and dispatch campaigns with higher precision. 

This requires database model additions, updates to the Excel background importer, new query filtering logic, API parameter validation, and frontend updates to integrate the new combobox widget.

## Goals / Non-Goals

**Goals:**
- Create the `SubArea` model.
- Link companies to `SubArea` (optional ForeignKey) and users to multiple `SubArea` filters (ManyToManyField).
- Extend the Excel importer to parse the `"sub actividad"` column, resolve/bulk-create `SubArea` records, and link them to companies in bulk.
- Update `/api/companies/filter-options/`, `/api/companies/available-filters/`, and `/api/companies/count/` to support sub-activities.
- Register `SubArea` in Django admin; add `sub_area` to `CompanyAdmin.list_filter` and `sub_area_filters` to `UserAdmin.filter_horizontal`.
- Integrate the new combobox into the landing page hero and the dashboard filters.
- Update `combobox.js` to initialize, count, and cross-filter the third combobox dimension.
- Enforce the new sub-area filters in the automated email dispatch tasks.
- Update `update_filters` view to persist `sub_area_filters` and `_serialize_user` to include them in GDPR export.

**Non-Goals:**
- Creating a strict parent-child ForeignKey relationship between `SubArea` and `Area` at the database constraint level. They will be resolved independently, but cross-filtering will be handled dynamically via the `get_available_filters` query.

## Decisions

### 1. Database Model for Sub-Activities
Create a new model `SubArea` in `apps/companies/models.py` that inherits from `LowercaseFieldsMixin`. It will have a unique lowercase `name` field, mirroring the design of `Area` and `Location`.
*Rationale*: This is a simple, proven pattern in this codebase. Using a database-backed taxonomy model prevents duplicate variations, makes options enumeration trivial, and allows efficient ForeignKey matches.

### 2. Whitelist Validation in Views & Whitelist Caching
Validate `sub_area` GET/POST inputs against `get_filter_options()["sub_areas"]`.
*Rationale*: This prevents malicious clients from bypassing the combobox and submitting arbitrary search strings. Caching is handled inside `get_filter_options()` using Django's cache backend (Redis), ensuring we do not query the database on every visitor page load.

### 3. Bulk Importing for Sub-Activities
Extend `import_companies_from_xlsx` to process the `"sub actividad"` column. Collect unique values per chunk, resolve/bulk-create them in the database using the shared `_resolve_taxonomy` helper, and write them in bulk.
*Rationale*: Using `bulk_create` and `bulk_update` is critical for performance. The chunk-based transactions preserve progress and prevent timeout errors.

### 4. Column Header Normalization
The Excel column header `"SUB ACTIVIDAD"` is normalized by `importers.py:227`: `str(h).strip().lower()` → `"sub actividad"` (lowercased, space preserved). The `_parse_row` lookup key must match this normalized form exactly: `get("sub actividad")`.
*Rationale*: The existing normalization at line 227 already strips whitespace and lowercases all headers, producing space-separated lowercase keys. Any new column must use the same normalized key for the `header_map` lookup.

### 5. JavaScript Controller: Third Combobox Integration
The existing `combobox.js` is fully generic in its core loop (`initCombobox` accepts any `data-combobox` type), but the orchestration functions (`initWidgets`, `scheduleCount`, `scheduleAvailableFilters`) hardcode area/location selectors. The implementation must:

- Add `"sub_area"` to the `noFilterLabel` ternary in `initCombobox` → `'— TODAS LAS SUBACTIVIDADES —'`.
- In `initWidgets`: query `[data-combobox="sub_area"]` and pass `opts.sub_areas` to `initCombobox`.
- In `scheduleCount`: query `[data-combobox="sub_area"] input[type=hidden]` and append `sub_area` params.
- In `scheduleAvailableFilters`: query `[data-combobox="sub_area"] input[type=hidden]`, append `sub_area` params, and call `_updateOptions(data.sub_areas)` on the sub_area container.

*Rationale*: Keeping the core widget factory generic while updating the orchestration layer follows the existing pattern. The `_updateOptions` and hidden-input mechanisms are already dimension-agnostic.

### 6. Cross-Dimensional Filtering for Three Dimensions
The current `get_available_filters` performs 2D cross-filtering (areas ↔ locations). With sub_areas as a third dimension, the logic expands to three queries:

- **available_areas**: areas whose companies match selected locations AND selected sub_areas.
- **available_locations**: locations whose companies match selected areas AND selected sub_areas.
- **available_sub_areas**: sub_areas whose companies match selected areas AND selected locations.

Each is built as a filtered queryset on the taxonomy model using `company__area__name__in`, `company__location__name__in`, and `company__sub_area__name__in` reverse relations. The cache key includes all three dimensions. When no filters are selected, fall back to `get_filter_options()`.
*Rationale*: Going through `Company`'s reverse relations (e.g., `Area.objects.filter(companies__location__name__in=...)`) is the same pattern as the existing 2D code, extended naturally.

## Risks / Trade-offs

- **[Risk]** → Higher memory usage and CPU latency in `get_available_filters` due to the third query dimension.
  - *Mitigation*: Ensure fields are queried using `.values_list("name", flat=True)` and cached for 60 seconds.
- **[Risk]** → Missing column `"sub actividad"` in some uploaded Excel files causes imports to fail.
  - *Mitigation*: Treat the `"sub actividad"` column as optional in `_parse_row`. If it is missing from `header_map`, default it to an empty string. The `sub_area` FK on `Company` is nullable, so missing data means `sub_area=None`.
- **[Risk]** → Existing `combobox.js` orchestration functions (`scheduleCount`, `scheduleAvailableFilters`, `initWidgets`) hardcode area/location selectors. If the sub_area wiring is missed, the third combobox renders but does not affect count or cross-filtering.
  - *Mitigation*: Each of the three orchestration functions must be updated in lockstep. The task list explicitly enumerates each function change to prevent omission.
