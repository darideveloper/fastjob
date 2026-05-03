# Proposal: fix-build-time-settings-defaults

## Why

`RUN python manage.py collectstatic` runs during the Docker image build, before any runtime env
vars are available. Two settings — `SITE_DOMAIN` and `CSRF_TRUSTED_ORIGINS` — had no `default=`
values, causing `python-decouple` to raise `UndefinedValueError` and abort every Coolify
deployment. Additionally, both variables were missing from the Coolify env var configuration
entirely, meaning they would also fail at runtime.

## What Changes

- `config/settings.py:107`: `SITE_DOMAIN` gains `default="localhost"`
- `config/settings.py:341`: `CSRF_TRUSTED_ORIGINS` gains `default="http://localhost"`
- Coolify env vars: `SITE_DOMAIN` and `CSRF_TRUSTED_ORIGINS` must be added manually

## Problem

`RUN python manage.py collectstatic` executes during the Docker image build. Django imports
`config/settings.py` at module scope to bootstrap `manage.py`. Any `config("VAR")` call without
a `default=` crashes immediately when the variable is absent from the build container's
environment — which is always the case for runtime-only env vars injected via `docker-compose.yml`.

Two top-level variables have no defaults and crash the build in sequence:

1. `SITE_DOMAIN` (`settings.py:107`) — no `default=`, also absent from Coolify env vars
2. `CSRF_TRUSTED_ORIGINS` (`settings.py:341`) — no `default=`, also absent from Coolify env vars

A compounding problem: the validation guard at line 344 raises `ImproperlyConfigured` when any of
the three guarded vars (`ALLOWED_HOSTS`, `SITE_DOMAIN`, `CSRF_TRUSTED_ORIGINS`) are falsy. This
means empty-string defaults are insufficient — the defaults must be non-empty placeholder values.

Additionally, both variables are missing from the Coolify environment variable configuration, so
even a successful build would fail at runtime.

## Solution

Add build-safe, non-empty defaults to both variables in `settings.py`:

- `SITE_DOMAIN`: `default="localhost"` — truthy, overridden at runtime by Coolify
- `CSRF_TRUSTED_ORIGINS`: `default="http://localhost"` — satisfies `Csv()` cast and truthy check

Also document the two Coolify env vars that must be added for production.

## Scope

- **Modified:** `config/settings.py` (2 lines)
- **No changes** to `Dockerfile`, `docker-compose.yml`, or any other file
- **No new dependencies**

## Coolify env vars required (manual step)

| Variable | Production value |
|----------|-----------------|
| `SITE_DOMAIN` | `fastjob.apps.darideveloper.com` |
| `CSRF_TRUSTED_ORIGINS` | `https://fastjob.apps.darideveloper.com` |

## Why these defaults are safe

The defaults are only active during `collectstatic` at build time. `collectstatic` does not serve
HTTP requests, so `ALLOWED_HOSTS`, `SITE_DOMAIN`, and `CSRF_TRUSTED_ORIGINS` are never used for
actual request validation during the build step. At container start, Coolify injects the real
values, which override the defaults completely.
