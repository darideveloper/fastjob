## Why

Currently, the application allows filtering companies by broad Sectors (Area) and Locations. However, companies within a single sector often have very different specialties (e.g. Area: "seller", Sub-Activity: "cleaning products"). This change allows importing, storing, and filtering by specific sub-activities ("sub actividad") so that users can direct their CVs to more targeted matches and improve their campaign relevance.

## What Changes

- **Database & Django Admin**: 
  - Add a new `SubArea` model (storing name, inheriting `LowercaseFieldsMixin`, no FK to `Area`) and link it to the `Company` model via a new nullable `sub_area` ForeignKey (`on_delete=SET_NULL`).
  - Extend the `User` model with a ManyToMany relationship to `SubArea` (named `sub_area_filters`) to persist their selected sub-activities.
  - Register `SubArea` in Django admin; add `sub_area` to `CompanyAdmin.list_filter` and `sub_area_filters` to `UserAdmin.filter_horizontal`.
  - Override model verbose names in the admin UI (`Area` to "Área/Áreas" and `SubArea` to "Subárea/Subáreas") dynamically in [admin.py](file:///mnt/hd/develop/django/fastjob/apps/companies/admin.py) without modifying the database models.
- **Excel Importer**: Expand `_parse_row` to extract the `"sub actividad"` column (lowercased, space-preserved header key) into a new `sub_area_name` field. Update `_process_chunk` to resolve/bulk-create `SubArea` records via `_resolve_taxonomy` with a new `sub_area_cache`, and include `sub_area` in `COMPANY_UPDATE_FIELDS` and company payloads.
- **Backend Queries**:
  - Update `get_filter_options` to query and cache all sub-activities (returning `"sub_areas"` key).
  - Update `matching_companies_qs` and `get_company_count` to accept and filter by `sub_areas` with case-insensitive exact match.
  - Update `get_available_filters` to handle 3D cross-dimensional filtering (areas, locations, sub-areas) and include `"sub_areas"` in the result.
- **API endpoints**: Update `available_filters_view` and `companies_count_view` to read, whitelist-validate, and pass `sub_area` GET parameters.
- **Mailing Engine**: Update `process_mailing_queue` to pass `user.sub_area_filters.all()` into `matching_companies_qs`.
- **JavaScript Controller** (`static/js/combobox.js`):
  - Add `"sub_area"` to the `noFilterLabel` ternary (`'— TODAS LAS SUBACTIVIDADES —'`).
  - Update `initWidgets` to discover and initialize `[data-combobox="sub_area"]` containers.
  - Update `scheduleCount` to collect hidden inputs from `[data-combobox="sub_area"]` and append `sub_area` params.
  - Update `scheduleAvailableFilters` to send `sub_area` params and update the sub-area container with `data.sub_areas`.
- **Templates**:
  - `templates/home.html`: Add the third `data-combobox="sub_area"` combobox div (with `data-name="sub_area"`, placeholder `"Escribe o elige una subactividad (ej. Productos de limpieza)…"`) between the location combobox and the company counter.
  - `templates/dashboard/index.html`: Add the third combobox div inside the filter form (`data-name="sub_area_filter"`, `data-value` populated from `user.sub_area_filters.all`).
- **Dashboard Views**: Update `update_filters` to parse, validate, and persist `sub_area_filter` POST data; update `_serialize_user` to include `sub_area_filters` in GDPR exports.
- **Testing**:
  - Add unit and view tests covering Excel importing of subactivities, query cross-filtering, API query parameter whitelist validation, and dashboard filter settings.

## Capabilities

### New Capabilities
<!-- None needed as we are modifying existing features -->

### Modified Capabilities
- `companies`: Support parsing `"sub actividad"` from Excel, resolving its taxonomy, and querying/counting companies by sub-area.
- `dashboard`: Add a `sub_area` filter combobox to the dashboard, validate submissions, and serialize the filter in GDPR exports.
- `landing`: Add a `sub_area` filter combobox to the landing page finder.
- `mailing`: Filter companies by the user's selected sub-areas during automated email dispatch.

## Impact

- **Affected Models**: `Company`, `User`, and the new `SubArea` model.
- **Import flow**: Background Celery task `process_company_import` and `import_companies_from_xlsx`.
- **API endpoints**: `/api/companies/filter-options/`, `/api/companies/available-filters/`, and `/api/companies/count/`.
- **Campaign logic**: `process_mailing_queue` Celery task.
- **JS Controller**: `static/js/combobox.js` needs to track the third combobox widget and pass it to count/filtering requests.
