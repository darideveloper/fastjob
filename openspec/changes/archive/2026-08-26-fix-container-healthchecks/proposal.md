# Proposal: Fix Container Healthchecks for Non-Web Services

## Why

In production, Coolify and Netdata report `celery_worker`, `celery_beat`, and `flower` as **unhealthy** even though they run correctly (beat schedules `process-mailing-queue` every minute, the worker succeeds tasks in ~10 ms, flower serves on 5555). The cause is a wrong health signal, not a service failure: those three services inherit the Dockerfile's global `HEALTHCHECK` that curls `http://localhost:8000/healthz` — a port none of them serves — so Docker always marks them unhealthy and Netdata raises `docker_container_unhealthy` alerts.

## What Changes

1. **Remove the global `HEALTHCHECK` from `Dockerfile`** (lines 38-39) so no service can silently inherit a check that assumes the web role. A service without a check then shows "no health status" instead of a false "unhealthy".
2. **Add a compose `healthcheck` to `celery_worker`** using `celery -A config inspect ping -d celery@$$HOSTNAME` (real liveness via the broker, scoped to the container itself).
3. **Add a compose `healthcheck` to `celery_beat`** verifying PID 1 is the beat process (`grep -aq beat /proc/1/cmdline`), since beat exposes no control/ping interface.
4. **Add `FLOWER_BASIC_AUTH` to the `flower` environment** (today it exists only in the CLI arg, so it is not available at runtime) and **add a `healthcheck`** that curls the dashboard with auth (`curl -fsS -L -u "$$FLOWER_BASIC_AUTH" http://127.0.0.1:5555/flower/`).
5. **Update the `infrastructure` spec** with requirements for accurate per-service healthchecks and for orchestrator/Netdata health status reflecting real liveness.
6. **Update deployment docs** (`docs/deploy.md`, `docs/features/monitoring.md`) to describe the new healthcheck behavior.

## Capabilities

### New Capabilities
<!-- None introduced. -->

### Modified Capabilities
- `infrastructure`: add requirements for accurate healthchecks on non-HTTP services and for the absence of a false-unhealthy image-level default.

## Impact

- **`Dockerfile`**: removes the global `HEALTHCHECK` block.
- **`docker-compose.yml`**: adds `healthcheck` blocks to `celery_worker`, `celery_beat`, `flower`; adds `FLOWER_BASIC_AUTH` to `flower`'s environment. `db`, `redis`, and `web` healthchecks are unchanged.
- **Runtime behavior**: none. This is purely a monitoring/orchestration signal fix; no application code changes.
- **Systems**: Coolify dashboard status, Netdata `docker_container_unhealthy` alerts (clear automatically once containers report healthy).