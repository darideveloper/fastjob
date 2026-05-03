# Tasks

## 1. Database & Taxonomy
- [x] 1.1 Create `Area` and `Location` models in `apps/companies/models.py`.
- [x] 1.2 Add FK fields to `Company` and `User` (temporary names like `area_fk`, `location_fk`).
- [x] 1.3 Create a data migration to populate `Area`/`Location` from existing `Company` data and link them.
- [x] 1.4 Remove old `CharField` fields and rename FKs to `area` and `location`.
- [x] 1.5 Update `apps/companies/admin.py` to include `Area` and `Location` admins.

## 2. API & Backend Queries
- [x] 2.1 Update `apps/companies/queries.py` (`get_filter_options`, `matching_companies_qs`, `get_company_count`) to use the new models.
- [x] 2.2 Update `apps/companies/views.py` to ensure validation works with the new taxonomy.
- [x] 2.3 Update `apps/companies/importers.py` to handle `Area`/`Location` lookup during Excel import.

## 3. Admin & User Interface
- [x] 3.1 Update `apps/accounts/admin.py` to use dropdowns for `area_filter` and `location_filter` in the `User` change form.
- [x] 3.2 Update `apps/dashboard/views.py` (`update_filters`) to validate against the new models.
- [x] 3.3 Verify `combobox.js` works with the new API structure (may need to switch from names to IDs in the `data-value` attributes).

## 4. Layout Refinement
- [x] 4.1 Update `templates/home.html` to place the company counter "next to" the filter inputs (e.g., in a single row layout).
- [x] 4.2 Update `templates/dashboard/index.html` to refine the counter placement.
- [x] 4.3 Ensure a "Sin filtro" (empty) option is always available and works correctly.

## 5. Verification
- [x] 5.1 Run all existing tests (`pytest`) and ensure no regressions in mailing engine or dashboard.
- [x] 5.2 Add a new test suite `apps/companies/tests/test_taxonomy.py` covering the new models and FK constraints.
- [x] 5.3 Verify the "custom values rejection" in both Dashboard and Landing API.
- [x] 5.4 Manual audit of the Django Admin User form to confirm dropdowns are present and functional.
