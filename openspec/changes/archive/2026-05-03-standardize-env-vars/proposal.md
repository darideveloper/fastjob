# Change: Standardize Environment Variables and Scaling Configuration

## Why
There are several discrepancies between the documented environment variables, the `.env.example` file, and the actual implementation in `docker-compose.yml` and `settings.py`. Specifically, the scaling mechanism for Celery workers documented in `docs/deploy.md` is currently non-functional because concurrency is hardcoded in the Docker configuration. Additionally, the backup script relies on individual database variables while the application uses `DATABASE_URL`, leading to potential configuration drift.

## What Changes
- **Infrastructure**: Implement `CELERY_WORKER_CONCURRENCY` support in `docker-compose.yml` and `settings.py`.
- **Configuration**: Standardize `.env.example` to include missing OAuth and site configuration variables.
- **Documentation**: Update `docs/deploy.md` to accurately reflect all environment variables used by the system and their purposes.
- **Deployment**: Synchronize the backup script's variable requirements with the main application configuration where possible, or document the dual requirement clearly.

## Impact
- Affected specs: `infrastructure` (new), `dev-environment` (documentation only)
- Affected code: `docker-compose.yml`, `config/settings.py`, `.env.example`, `docs/deploy.md`, `scripts/backup_db.sh`
