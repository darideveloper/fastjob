# Tasks for Multiple Filters

## 1. Database Schema & Data Migration
- [x] 1.1 In `apps/accounts/models.py`, add `area_filters` and `location_filters` as `ManyToManyField` to `User`.
- [x] 1.2 Generate schema migration for the new fields (`makemigrations accounts`).
- [x] 1.3 Create a data migration to iterate over all users, and if `area_filter` is not null, add it to `area_filters`. Repeat for `location_filter`.
- [x] 1.4 Generate schema migration to remove the old `area_filter` and `location_filter` `ForeignKey` fields from `User`.

## 2. Query, API & Cache Updates
- [x] 2.1 Update `matching_companies_qs` in `apps/companies/queries.py` to accept lists/QuerySets of areas/locations and filter using `__in`.
- [x] 2.2 Update `get_company_count` in `apps/companies/queries.py` to generate a stable cache key from sorted lists of area/location names.
- [x] 2.3 Update `companies_count_view` in `apps/companies/views.py` to extract multiple values using `request.GET.getlist("area")` and `request.GET.getlist("location")`. Validate each against `allowed_areas` and `allowed_locations`.
- [x] 2.4 Fix tests in `apps/companies/tests/test_queries.py` and `apps/companies/tests/test_views.py` to reflect the new list-based arguments.

## 3. Backend Dashboard View & Admin
- [x] 3.1 Update `update_filters` in `apps/dashboard/views.py` to extract multiple values using `request.POST.getlist("area_filter")` and `request.POST.getlist("location_filter")`.
- [x] 3.2 Validate each value against the allowed options, then update `user.area_filters.set(area_objs)` and `user.location_filters.set(location_objs)`.
- [x] 3.3 Update `apps/accounts/admin.py` to remove `area_filter` and `location_filter` from `fieldsets` and `list_display`, and add `area_filters` and `location_filters` to `filter_horizontal`.
- [x] 3.4 Fix tests in `apps/dashboard/tests/test_filters.py` for multi-select behaviour.

## 4. Frontend UI
- [x] 4.1 Update `combobox.js` to support selecting multiple items, displaying them as removable pills.
- [x] 4.2 Modify the form serialization in the UI so that multiple `name="area_filter"` and `name="location_filter"` inputs are submitted.
- [x] 4.3 Update `templates/dashboard/index.html` and `templates/home.html` (Landing) to initialize the combobox with multiple existing selections (e.g., using a comma-separated list in a data attribute or JSON in a script tag).
- [x] 4.4 Update the `data-value` bindings in the templates to output all selected names.

## 5. Mailing Engine
- [x] 5.1 In `apps/mailing/tasks.py`, change the call to `matching_companies_qs(user.area_filters.all(), user.location_filters.all())`.
- [x] 5.2 Fix tests in `apps/mailing/tests/test_tasks.py` to set up multiple filters using `.add()`.
