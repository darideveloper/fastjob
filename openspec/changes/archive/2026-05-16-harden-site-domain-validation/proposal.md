# Change: Harden SITE_DOMAIN Validation to Prevent Localhost Unsubscribe URLs

## Why

Outbound CV emails contain unsubscribe links built from `SITE_DOMAIN` in `apps/mailing/engine.py:383-384`. When `SITE_DOMAIN` is absent from the runtime environment, python-decouple falls back to its hard-coded default `"localhost"`, producing broken links like `https://localhost/unsubscribe/<token>/`. The existing guard in `config/settings.py:363` only checks for falsy values — `"localhost"` is truthy and passes silently, so the application starts and sends emails with an uncreachable unsubscribe URL. The spec requirement `Consistent Site Identity for Django Services` is already violated: its scenario explicitly states workers MUST NOT fall back to `https://localhost/`.

The tension with the *build-time importability* requirement (`Django settings SHALL be importable at Docker build time`) is resolved by running `collectstatic` under `DEBUG=True`, which puts the new guard into dev-mode (where localhost is acceptable) during the build stage.

## What Changes

- **`Dockerfile:30`** — change `RUN python manage.py collectstatic --noinput` to `RUN DEBUG=True python manage.py collectstatic --noinput`, so the Docker build is not blocked by the new runtime guard.
- **`config/settings.py`** — after the existing falsy-value guard, add a second guard: when `DEBUG=False` and `SITE_DOMAIN` resolves to a placeholder hostname (`localhost` or `127.0.0.1`), raise `ImproperlyConfigured` with a clear operator message.
- **`apps/mailing/tests/test_url_scheme.py`** — extend with two new test cases: one asserting that the guard fires in production mode with a placeholder domain, and one asserting that local dev with `DEBUG=True` and `SITE_DOMAIN=fastjob.localhost:8000` passes.
- **Infrastructure spec (MODIFIED)** — update the *build-time importability* requirement to reflect that the Docker build now uses `DEBUG=True` for `collectstatic`.
- **Infrastructure spec (ADDED)** — add a new `Requirement: Production Startup Guard for Placeholder SITE_DOMAIN` to the `infrastructure` capability.

## Impact

- **Affected specs:** `infrastructure`
- **Affected code:**
  - `Dockerfile` (1-line change to the collectstatic RUN step)
  - `config/settings.py` (3–5 lines after the existing guard)
  - `apps/mailing/tests/test_url_scheme.py` (2 new test functions)
- **No migration needed** — this is a startup-time validation; no schema or data changes.
- **Breaking for misconfigured deployments** — a production deployment where `SITE_DOMAIN` is missing or set to `localhost` will refuse to start. This is intentional fail-loud behavior.
