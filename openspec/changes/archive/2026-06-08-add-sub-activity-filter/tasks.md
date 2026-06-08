## 1. Database Schema & Migrations

- [x] 1.1 Create the `SubArea` model in `apps/companies/models.py` (inherits `LowercaseFieldsMixin`, unique `name` field, no FK to `Area`).
- [x] 1.2 Add the `sub_area` ForeignKey field pointing to `SubArea` on the `Company` model (`null=True, blank=True, on_delete=SET_NULL`, `related_name="companies"`).
- [x] 1.3 Add the `sub_area_filters` ManyToManyField to `User` in `apps/accounts/models.py` (`blank=True`, `related_name="users_m2m"`).
- [x] 1.4 Run `python manage.py makemigrations` and `python manage.py migrate`.

## 2. Excel Importer updates

- [x] 2.1 In `_parse_row`, add extraction of `get("sub actividad")` (lowercased, space-preserved normalized header key) → `sub_area_name`. Add `"sub_area_name"` to the returned dict.
- [x] 2.2 Update `_process_chunk` signature to accept a `sub_area_cache` dict param. Resolve distinct `SubArea` names via `_resolve_taxonomy(SubArea, distinct_sub_areas, sub_area_cache)`. Include `sub_area` in `company_kwargs` using `sub_area_cache.get(r["sub_area_name"])`.
- [x] 2.3 Create `sub_area_cache = {}` in `import_companies_from_xlsx` and pass it to every `_process_chunk` call in `flush()`.
- [x] 2.4 Add `"sub_area"` to the `COMPANY_UPDATE_FIELDS` list.

## 3. Query Logic & Whitelist Validation

- [x] 3.1 Update `get_filter_options` in `apps/companies/queries.py` to retrieve, sort, and cache all `SubArea` entries (returning `"sub_areas"` key alongside `"areas"` and `"locations"`).
- [x] 3.2 Update `matching_companies_qs` to accept `sub_areas=None`, with the same type-normalization pattern (`values_list` / list / scalar), apply `qs.filter(sub_area__name__in=sub_areas)`.
- [x] 3.3 Update `get_company_count` to accept `sub_areas` param, include it in stable cache key (`sub_area_key`), and pass it to `matching_companies_qs`.
- [x] 3.4 Update `get_available_filters` to accept `sub_areas` param, include it in cache key hashing, and return `"sub_areas"` in the result from 3D cross-filtering queries:
  - `available_areas`: filter by selected locations AND selected sub_areas
  - `available_locations`: filter by selected areas AND selected sub_areas
  - `available_sub_areas`: filter by selected areas AND selected locations

## 4. API Endpoints

- [x] 4.1 Update `available_filters_view` and `companies_count_view` in `apps/companies/views.py` to read `request.GET.getlist("sub_area")`, validate against `options["sub_areas"]` whitelist, and pass to `get_available_filters` / `get_company_count`.

## 5. Campaign Outbound Emails

- [x] 5.1 Update `process_mailing_queue` in `apps/mailing/tasks.py` to pass `user.sub_area_filters.all()` as the third argument to `matching_companies_qs`.

## 6. Client Dashboard Settings

- [x] 6.1 Update `update_filters` in `apps/dashboard/views.py` to read `request.POST.getlist("sub_area_filter")`, validate against `options["sub_areas"]` whitelist, resolve via `SubArea.objects.get(name__iexact=...)`, and persist via `user.sub_area_filters.set(sub_area_objs)` inside the transaction.
- [x] 6.2 Update `_serialize_user` in `apps/dashboard/views.py` to include `"sub_area_filters": list(user.sub_area_filters.values_list("name", flat=True))`.

## 7. Django Admin Config

- [x] 7.1 Register `SubArea` in `apps/companies/admin.py` (minimal admin following `AreaAdmin` pattern).
- [x] 7.2 Add `"sub_area"` to `CompanyAdmin.list_filter` tuple in `apps/companies/admin.py`.
- [x] 7.3 Add `sub_area_filters` to `UserAdmin.filter_horizontal` list and to the "Datos FastJob" fieldsets in `apps/accounts/admin.py`.

## 8. Templates

- [x] 8.1 In `templates/home.html`, add the sub_area combobox between the location combobox and the company counter counter div:
  ```html
  <div class="flex-1 text-left w-full">
    <label class="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2 ml-1">Subactividad</label>
    <div data-combobox="sub_area"
         data-name="sub_area"
         data-value=""
         data-placeholder="Escribe o elige una subactividad (ej. Productos de limpieza)…"></div>
  </div>
  ```
- [x] 8.2 In `templates/dashboard/index.html`, add the sub_area combobox after the location combobox inside the `space-y-4` div:
  ```html
  <div>
    <label class="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-1.5 ml-1">Subactividad</label>
    <div data-combobox="sub_area"
         data-name="sub_area_filter"
         data-value="{% for s in user.sub_area_filters.all %}{{ s.name }}{% if not forloop.last %},{% endif %}{% endfor %}"
         data-placeholder="Escribe o elige una subactividad (ej. Productos de limpieza)…"></div>
  </div>
  ```

## 9. JavaScript Controller

- [x] 9.1 Update `noFilterLabel` ternary in `initCombobox` (`combobox.js:37`): add `comboboxType === 'sub_area' ? '— TODAS LAS SUBACTIVIDADES —'` branch before the fallback.
- [x] 9.2 Update `initWidgets` (`combobox.js:300-320`): query `widget.querySelector('[data-combobox="sub_area"]')`, pass `opts.sub_areas` to `initCombobox`, and include it in the `onChange` closure.
- [x] 9.3 Update `scheduleCount` (`combobox.js:230-260`): add `var subAreaInputs = widget.querySelectorAll('[data-combobox="sub_area"] input[type=hidden]')` and append `params.append('sub_area', input.value)` in the loop.
- [x] 9.4 Update `scheduleAvailableFilters` (`combobox.js:262-298`): collect `[data-combobox="sub_area"] input[type=hidden]`, append `sub_area` params, update the sub_area container via `_updateOptions(data.sub_areas)`, and check `data.sub_areas` in the guard clause alongside `data.areas` and `data.locations`.

## 10. Testing & Verification

- [x] 10.1 Run all company, mailing, and dashboard test suites using `pytest` to verify the implementation.
