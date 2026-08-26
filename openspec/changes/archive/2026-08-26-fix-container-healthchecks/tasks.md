# Tasks: Fix Container Healthchecks

## 1. Infrastructure Specification

- [x] Add requirements to `specs/infrastructure/spec.md` for accurate per-service healthchecks, no false-unhealthy from inherited checks, and orchestrator/Netdata health status reflecting real liveness.

## 2. Dockerfile

- [x] 2.1 Remove the global `HEALTHCHECK` block (lines 38-39) that curls `localhost:8000/healthz`.

## 3. docker-compose.yml — celery_worker

- [x] 3.1 Add a `healthcheck` to `celery_worker`:
      `test: ['CMD-SHELL', 'celery -A config inspect ping -d celery@$$HOSTNAME --timeout=10 | grep -q pong']`
      with `interval: 30s`, `timeout: 15s`, `start_period: 45s`, `retries: 3`.

## 4. docker-compose.yml — celery_beat

- [x] 4.1 Add a `healthcheck` to `celery_beat`:
      `test: ['CMD-SHELL', 'grep -aq beat /proc/1/cmdline']`
      with `interval: 30s`, `timeout: 5s`, `start_period: 30s`, `retries: 3`.

## 5. docker-compose.yml — flower

- [x] 5.1 Add `FLOWER_BASIC_AUTH=${FLOWER_BASIC_AUTH:?FLOWER_BASIC_AUTH must be set}` to the `flower` service `environment` block.
- [x] 5.2 Add a `healthcheck` to `flower`:
      `test: ['CMD-SHELL', 'curl -fsS -L -u "$$FLOWER_BASIC_AUTH" http://127.0.0.1:5555/flower/']`
      with `interval: 30s`, `timeout: 5s`, `start_period: 30s`, `retries: 3`.

## 6. Documentation

- [x] 6.1 Update `docs/deploy.md` to describe the worker/beat/flower healthcheck behavior (replaces the inherited web-only check).
- [x] 6.2 Update `docs/features/monitoring.md` to describe the new per-service healthcheck behavior.

## 7. Validation

- [x] 7.1 Run `docker compose config -q` and confirm the YAML and env interpolation are valid. Ensure the required env vars are available first (e.g. `cp .env.example .env`), otherwise interpolation of `${VAR:?}` entries errors out.
- [x] 7.2 Redeploy via Coolify and confirm all containers report `healthy` within ~1-2 minutes.
- [x] 7.3 Confirm Netdata `docker_container_unhealthy` alerts clear.
- [x] 7.4 Observe logs for a few minutes to confirm beat still schedules and the worker still processes tasks.