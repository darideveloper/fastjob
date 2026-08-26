# Design: Fix Container Healthchecks

## Context

`Dockerfile` defines a global `HEALTHCHECK` (lines 38-39) that curls `http://localhost:8000/healthz`. In Docker, every container built from the image inherits this check **unless** the service overrides it in compose. Only `web` overrides it (`docker-compose.yml:100-104`). `celery_worker`, `celery_beat`, and `flower` define no healthcheck, so they inherit a check for a port they do not serve — Docker marks them unhealthy, Coolify shows `(unhealthy)`, and Netdata raises `docker_container_unhealthy`.

The containers are functionally healthy: beat schedules `process-mailing-queue` each minute, the worker succeeds tasks in milliseconds, and flower serves on 5555. The fix is a monitoring/orchestration signal correction, not an application fix.

## Goals / Non-Goals

**Goals:**
- Every service reports a health status that honestly reflects its actual runtime state.
- No service can silently inherit a healthcheck that assumes the web role.
- Checks are cheap, self-contained, and require no new dependencies (image already ships `curl`, `grep`, `python`, and the `celery` CLI).
- Compatible with the existing Coolify deployment (compose file passes through unchanged).

**Non-Goals:**
- No changes to worker/beat/flower application behavior or command semantics.
- No changes to `db`, `redis`, or `web` healthchecks (already correct).
- Not fixing unrelated host-level noise (Netdata postgres `netdata` role, Redis `vm.overcommit_memory`), which are outside this repo.

## Decisions

### Decision 1: Remove the global `HEALTHCHECK` from the Dockerfile

**Choice:** Delete the `HEALTHCHECK` block (lines 38-39).

**Rationale:** The image-level check is only correct for the web role, and `web` already overrides it in compose. Keeping it means every future non-web service must remember to override it — today's exact failure mode. After removal, a service without its own check shows **no health status**, which Docker and Netdata treat as not-unhealthy, which is strictly safer than a wrong check.

**Alternative considered:** Keep it as a "web default" for standalone `docker run`. Rejected as the root cause of the recurring confusion; nothing in this project runs the image standalone without a compose command.

### Decision 2: `celery_worker` uses `celery inspect ping` via the broker

```yaml
healthcheck:
  test: ['CMD-SHELL', 'celery -A config inspect ping -d celery@$$HOSTNAME --timeout=10 | grep -q pong']
  interval: 30s
  timeout: 15s
  start_period: 45s
  retries: 3
```

**Rationale:** `celery -A config inspect ping` boots Django (via `config/celery.py`'s `os.environ.setdefault` — no extra env needed) and broadcasts a control ping; a functioning worker replies `pong`. This proves both that the worker's control loop is alive **and** that it is connected to the broker — a mere process-existence check would not. `-d celery@$$HOSTNAME` scopes the ping to the container itself so scaled replicas each check their own health. `$$` is compose escaping resolved to `$HOSTNAME` at runtime (same pattern already used for `pg_isready` on line 20).

**Gotcha handled:** No `set -o pipefail`. Docker runs `CMD-SHELL` via `/bin/sh`, which on Debian is `dash` — and dash does not support `pipefail`. It is unnecessary anyway: if celery gets no `pong`, `grep` exits 1 and the check fails.

**Timing rationale:** Each check boots Django + touches the broker (~1-3 s), so 30s interval avoids needless load; 45s `start_period` absorbs worker boot + mingle so cold-start flakiness never flags unhealthy.

### Decision 3: `celery_beat` uses a PID-1 process-liveness check

```yaml
healthcheck:
  test: ['CMD-SHELL', 'grep -aq beat /proc/1/cmdline']
  interval: 30s
  timeout: 5s
  start_period: 30s
  retries: 3
```

**Rationale:** Beat exposes no control/ping endpoint and writes no heartbeat, so the meaningful cheap signal is "container PID 1 is still `celery ... beat`" (compose `command:` replaces the image CMD; the image has no ENTRYPOINT). `grep -aq beat /proc/1/cmdline` reads the NUL-separated args as binary — no quoting issues, no Python, no extra deps.

**Alternative considered:** A DB "ticking" probe that checks a periodic task's `last_run_at` is recent. Rejected as over-coupled and fragile: it breaks if the task is paused, renamed, or removed, and it conflates beat liveness with task cadence.

**Known limitation:** a wedged-but-alive beat still passes this check. Risk is low (beat is a stateless scheduler) and it is caught operationally by observing the mailing queue stall. Acceptable for now.

### Decision 4: `flower` healthchecks its dashboard with runtime auth

```yaml
environment:
  - FLOWER_BASIC_AUTH=${FLOWER_BASIC_AUTH:?FLOWER_BASIC_AUTH must be set}
healthcheck:
  test: ['CMD-SHELL', 'curl -fsS -L -u "$$FLOWER_BASIC_AUTH" http://127.0.0.1:5555/flower/']
  interval: 30s
  timeout: 5s
  start_period: 30s
  retries: 3
```

**Key discovery:** today `FLOWER_BASIC_AUTH` is only baked into the CLI arg (`docker-compose.yml:175`) and is **not** a container env var, so `$FLOWER_BASIC_AUTH` would be empty at runtime. It must be added to `environment` for the check to authenticate.

**Rationale for the URL/details:** the trailing slash avoids flower's `/flower` → `/flower/` 302 (which `curl -f` treats as an HTTP error); `-L` is harmless robustness. `$$FLOWER_BASIC_AUTH` resolves at runtime from the container env, so rotating the password never bakes a stale value into the deploy.

## Risks / Trade-offs

- [A wedged-but-alive beat passes the liveness check] → Low risk (stateless scheduler); detected by observing the mailing queue. A DB-ticking probe can be added later if ever needed.
- [`celery inspect ping` adds broker traffic every 30s] → Negligible: one lightweight control broadcast per interval per container; current mailing queue sends ~1 task/min.
- [Healthcheck spawns a full Django boot for worker checks] → ~1-3 s every 30s per container; acceptable, and why the interval is 30s rather than the web service's 10s.
- [Dash-style shell incompatibility with `pipefail`] → Avoided entirely by not using `pipefail`; the pipeline fails correctly on its own.

## Migration Plan

1. Apply compose + Dockerfile edits.
2. Validate locally with `docker compose config -q` (no containers needed).
3. Redeploy via Coolify; confirm all containers transition to `healthy` within ~1-2 minutes.
4. Confirm Netdata `docker_container_unhealthy` alerts clear on the next check.
5. Rollback: revert the commit and redeploy; the only effect of rollback is returning to the previous (false-unhealthy) status — no functional risk.

## Open Questions

None. Decisions were confirmed with the user during exploration: remove the Dockerfile `HEALTHCHECK` (root-cause fix) and use process liveness for beat.