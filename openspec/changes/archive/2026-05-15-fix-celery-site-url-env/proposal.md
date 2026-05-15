# Change: Fix Celery Site URL Environment Variables

## Why
In production, background tasks (like the mailing engine) are generating absolute URLs (such as unsubscribe links) with `localhost` instead of the actual domain (e.g., `https://localhost/unsubscribe/...`). This is because the `celery_worker` and `celery_beat` services in `docker-compose.yml` are missing the `SITE_DOMAIN` and `SITE_SCHEME` environment variables, causing them to fall back to the default values in `settings.py`.

## What Changes
- Update `docker-compose.yml` to include `SITE_DOMAIN`, `SITE_SCHEME`, `SITE_NAME`, and `DEBUG` in the `celery_worker` service environment.
- Update `docker-compose.yml` to include `SITE_DOMAIN`, `SITE_SCHEME`, `SITE_NAME`, and `DEBUG` in the `celery_beat` service environment.

## Impact
- Affected specs: `specs/infrastructure/spec.md`
- Affected code: `docker-compose.yml`
