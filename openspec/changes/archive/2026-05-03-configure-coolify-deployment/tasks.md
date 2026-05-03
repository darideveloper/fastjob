# Tasks: Configure Coolify Deployment

## 1. Infrastructure Specification
- [x] Create `openspec/specs/infrastructure/spec.md` to define deployment requirements.

## 2. Docker Compose Refactoring
- [x] Add Coolify Metadata Headers (documentation, slogan, category, tags, port).
- [x] Modify `docker-compose.yml` to remove dev-only volumes.
- [x] Add `healthcheck` to `db` service using `pg_isready`.
- [x] Add `healthcheck` to `redis` service using `redis-cli ping`.
- [x] Update `web` service:
    - [x] Add `SERVICE_URL_WEB_8000` to environment.
    - [x] Add `healthcheck` using `/healthz`.
    - [x] Configure `depends_on` to wait for `db` and `redis` to be healthy.
    - [x] Map all necessary environment variables explicitly from Coolify inputs, using `${VAR:?}` for secrets.
- [x] Update `celery_worker` and `celery_beat`:
    - [x] Configure `depends_on` to wait for `db` and `redis` to be healthy.
    - [x] Map necessary environment variables.
- [x] Update `flower` service:
    - [x] Add `SERVICE_URL_FLOWER_5555` to environment.
    - [x] Ensure `FLOWER_BASIC_AUTH` is mapped.
- [x] Implement `${COOLIFY_VOLUME_*}` for persistent data.

## 3. Documentation
- [x] Add "Deploying to Coolify" section to `docs/deploy.md`.
- [x] List required environment variables that must be set in Coolify UI.

## 4. Validation
- [x] Verify `docker-compose.yml` syntax.
- [x] Run a simulated deployment check (if possible, or manual review).
