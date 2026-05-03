# Design: Environment Variable Standardization

## Context
The project uses `python-decouple` for configuration and Docker Compose for deployment. Documentation and `.env.example` have drifted from the actual implementation, and some "documented" features (like scaling Celery concurrency via environment variables) are not actually implemented.

## Goals
- Make the `CELERY_WORKER_CONCURRENCY` env var functional.
- Ensure `docs/deploy.md` is the "source of truth" for production environment variables.
- Align `.env.example` with current code requirements.
- Resolve the inconsistency between `DATABASE_URL` (Django) and individual `DB_*` variables (Backup script).

## Decisions

### 1. Dynamic Celery Concurrency
Instead of hardcoding `-c 4` in `docker-compose.yml`, we will use the environment variable `${CELERY_WORKER_CONCURRENCY:-4}`. This allows operators to tune worker performance without modifying the compose file.

### 2. Dual Database Configuration
The backup script (`scripts/backup_db.sh`) requires `DB_HOST`, `DB_NAME`, etc., because `pg_dump` does not natively parse a `DATABASE_URL` string easily without extra dependencies like `pydantic` or manual parsing. 
- **Decision**: Keep both `DATABASE_URL` (for Django/`dj_database_url`) and individual `DB_*` variables.
- **Rationale**: `pg_dump` is a system utility; parsing a complex `DATABASE_URL` in a shell script is error-prone. We will clearly document that both are required in production for backups to work.

### 3. Missing OAuth and Site Vars
Add `GOOGLE_OAUTH_PROJECT_MODE`, `MICROSOFT_TENANT`, `SITE_NAME`, and `SITE_SCHEME` to `.env.example` and `docs/deploy.md`. These are currently functional in `settings.py` but "hidden" from the configuration templates.

## Risks / Trade-offs
- **Redundancy**: Having both `DATABASE_URL` and `DB_*` variables is redundant, but it's the safest way to support both Django and system-level `pg_dump` without complex shell parsing.

## Migration Plan
- Update `docker-compose.yml`.
- Update `config/settings.py` (optional, for visibility).
- Update `.env.example`.
- Update `docs/deploy.md`.
- No database migrations or breaking changes expected.
