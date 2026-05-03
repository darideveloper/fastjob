# Tasks: Update Company Import Format and Data Normalization

## Phase 1: Model Updates
- [x] Add new fields to `Company` model in `apps/companies/models.py`.
- [x] Implement lowercase normalization in `Company.save()`, `Area.save()`, and `Location.save()`.
- [x] Create and apply schema migration.

## Phase 2: Importer Refactoring
- [x] Update `import_companies_from_xlsx` in `apps/companies/importers.py` to support new headers and splitting logic.
- [x] Ensure the importer uses `.lower()` for all string fields and taxonomy lookups.
- [x] Update `EXPECTED_HEADERS` to match the new format (`email` and `empresa` should be mandatory).

## Phase 3: Data Migration
- [x] Create a data migration to lowercase all existing `Company`, `Area`, and `Location` records.

## Phase 4: Admin and UI
- [x] Update `CompanyAdmin` in `apps/companies/admin.py` to include new fields in `list_display` and `fieldsets`.
- [x] Update the import form help text.

## Phase 5: Validation
- [x] Update `apps/companies/tests/test_importers.py` with new test cases for Spanish headers and splitting logic.
- [x] Add a new test file `apps/companies/tests/test_normalization.py` to verify lowercase enforcement.
- [x] Run all tests and verify no regressions in `filter_options` or `companies_count` views.
