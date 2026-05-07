## MODIFIED Requirements
### Requirement: Private Storage Backend
- All end-user-uploaded files containing personally identifiable information (PII) — specifically CVs and any future user-submitted documents — MUST be stored in a private-access storage bucket with a `private` ACL and no public URL.
- Operator-uploaded administrative artifacts (e.g. company-import `.xlsx` files written from the Django admin) are NOT covered by this requirement; their storage policy is governed by the `companies` capability and by the `Shared Imports Volume Between Web and Worker` requirement defined in this same capability.

#### Scenario: User CV upload
- **GIVEN** an authenticated user uploading a CV
- **WHEN** the file is saved to the system
- **THEN** the file MUST be stored in the private S3 storage with `private` ACL
- **AND** no public URL should be available for the file

#### Scenario: Operator company-import upload is out of scope
- **GIVEN** an administrator uploading a company-import `.xlsx` file via the Django admin
- **WHEN** the file is saved to the system
- **THEN** this requirement does NOT constrain its storage backend
- **AND** the storage policy is governed by the `companies` capability spec and by the `Shared Imports Volume Between Web and Worker` requirement

## ADDED Requirements
### Requirement: Shared Imports Volume Between Web and Worker
The deployment topology SHALL provide a shared, writable filesystem path between the `web` (gunicorn) and `celery_worker` services, used exclusively for company-import file hand-off.
- The path MUST be the same on both services and resolvable via the `COMPANY_IMPORT_LOCAL_PATH` environment variable (default `/app/imports`).
- In Docker Compose deployments the path MUST be backed by a named volume (e.g. `imports_data`) mounted on both services.
- In non-Docker deployments (bare-metal, multi-host, PaaS) the path MUST be backed by a shared filesystem (NFS, EFS, or equivalent) such that a file written by `web` is readable by `celery_worker` within the time it takes the Celery task to start.
- The application MUST refuse to start the celery worker (or surface a `/healthz` warning) if the path is missing, not a directory, or not writable.

#### Scenario: Web writes a file, worker reads it
- **GIVEN** a Docker Compose deployment with `imports_data` mounted at `/app/imports` on both `web` and `celery_worker`
- **WHEN** `web` saves a file at `/app/imports/2026/05/06/sample.xlsx`
- **THEN** the `celery_worker` process MUST be able to read that exact path

#### Scenario: Missing volume surfaces a health-check warning
- **GIVEN** a deployment where `COMPANY_IMPORT_LOCAL_PATH` does not exist or is not writable on the worker container
- **WHEN** the platform polls `/healthz`
- **THEN** the response includes a non-fatal warning identifying the missing imports path
- **AND** the `manage.py check_company_import_storage` command exits with a non-zero status

#### Scenario: Path mismatch between web and worker is detected
- **GIVEN** `web` has `COMPANY_IMPORT_LOCAL_PATH=/app/imports` and `celery_worker` has `COMPANY_IMPORT_LOCAL_PATH=/srv/imports`
- **WHEN** an upload is attempted
- **THEN** the discrepancy is surfaced via the worker-side health check before processing fails opaquely on `FileNotFoundError`
