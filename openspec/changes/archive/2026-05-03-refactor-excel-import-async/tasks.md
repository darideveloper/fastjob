## 1. Implementation
- [x] 1.1 Create `CompanyImportBatch` model in `apps/companies/models.py` with `file`, `status`, `created_count`, `updated_count`, `error_log` (as a JSONField), and timestamps.
- [x] 1.2 Generate and run migrations for the new model.
- [x] 1.3 Register `CompanyImportBatch` in `apps/companies/admin.py` to allow admins to view the status of imports.
- [x] 1.4 Refactor `apps/companies/importers.py` to accept a local file path, and wrap the row loop in `transaction.atomic()` for database performance.
- [x] 1.5 Create a Celery task `process_company_import` in `apps/companies/tasks.py` that updates the batch status to PROCESSING, downloads the file to a local `NamedTemporaryFile`, calls the importer with the local path, and updates the batch with final counts/errors and COMPLETED/FAILED status.
- [x] 1.6 Update `CompanyAdmin.import_xlsx_view` to create the `CompanyImportBatch`, trigger the Celery task, and redirect with a feedback message informing the user that processing is happening in the background.
- [x] 1.7 Add tests in `apps/companies/tests/test_importers.py` and `test_tasks.py` to cover the async execution flow and batch status updates.