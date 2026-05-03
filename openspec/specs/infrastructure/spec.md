# infrastructure Specification

## Purpose
TBD - created by archiving change standardize-env-vars. Update Purpose after archive.
## Requirements
### Requirement: Tunable Celery Worker Concurrency
The system SHALL allow operators to configure the number of concurrent worker processes via the `CELERY_WORKER_CONCURRENCY` environment variable. This value MUST be passed to the Celery worker command in the containerized environment.

#### Scenario: Operator increases worker concurrency
- **GIVEN** the `celery_worker` service is running in Docker
- **WHEN** the `CELERY_WORKER_CONCURRENCY` environment variable is set to `8`
- **THEN** the Celery worker process starts with `--concurrency=8` (or `-c 8`)

### Requirement: Standardized Environment Variable Templates
The project MUST maintain a synchronized `.env.example` file and deployment documentation (`docs/deploy.md`) that include all required and optional environment variables used by the application, including OAuth project modes and site metadata.

#### Scenario: New developer sets up the project
- **WHEN** a developer copies `.env.example` to `.env`
- **THEN** they find placeholders for `GOOGLE_OAUTH_PROJECT_MODE`, `MICROSOFT_TENANT`, and `SITE_NAME`, allowing them to configure these without digging into `settings.py`.

### Requirement: Redundant Database Configuration for Backups
The system MUST support both a unified `DATABASE_URL` for application connectivity and individual `DB_*` variables for system-level backup utilities (`pg_dump`). Both sets MUST be documented as required for production environments.

#### Scenario: Production backup script execution
- **GIVEN** the production `.env` contains both `DATABASE_URL` and `DB_PASSWORD`
- **WHEN** `scripts/backup_db.sh` is executed
- **THEN** it successfully connects to the database using the individual `DB_*` variables.

