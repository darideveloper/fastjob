## 1. Code Changes
- [x] 1.1 Update `docker-compose.yml` to use `${CELERY_WORKER_CONCURRENCY:-4}` for the `celery_worker` service.
- [x] 1.2 Update `config/settings.py` to optionally read `CELERY_WORKER_CONCURRENCY` (mostly for documentation/visibility, as Docker handles the command).

## 2. Configuration Templates
- [x] 2.1 Update `.env.example` to include:
    - `GOOGLE_OAUTH_PROJECT_MODE`
    - `MICROSOFT_TENANT`
    - `SITE_NAME`
    - `SITE_SCHEME`
    - `CELERY_WORKER_CONCURRENCY`
    - `BACKUP_BUCKET` (required by backup script)

## 3. Documentation
- [x] 3.1 Update `docs/deploy.md` "Critical values" table to include `DATABASE_URL`.
- [x] 3.2 Update `docs/deploy.md` reference table to include all missing variables.
- [x] 3.3 Ensure `docs/deploy.md` clearly states that both `DATABASE_URL` and `DB_*` variables are needed for backups.

## 4. Validation
- [x] 4.1 Verify `docker-compose config` shows the expected command for `celery_worker`.
- [x] 4.2 Run `manage.py check` to ensure no settings regression.
- [x] 4.3 Verify `docs/deploy.md` renders correctly.
