# Change: Asynchronous Excel Import for Companies

## Why
The current Excel import process runs synchronously in the Django Admin request cycle. When importing large files with thousands of rows, the process exceeds typical proxy/load balancer timeouts (e.g., 30-60 seconds), leading to `504 Gateway Timeout` errors in production. A background processing approach is required to guarantee reliable imports and provide a good user experience.

## What Changes
- Create a new `CompanyImportBatch` model to track file uploads and processing status (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`).
- Refactor the import view to save the file and enqueue a Celery task, immediately redirecting the admin with a status message.
- Implement a Celery task to process the file in the background, updating the batch status and recording metrics (created, updated, error messages).
- **BREAKING**: The admin view will no longer return import results synchronously.

## Impact
- Affected specs: `companies`
- Affected code: `apps/companies/models.py`, `apps/companies/admin.py`, `apps/companies/importers.py`, `apps/companies/tasks.py`