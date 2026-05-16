## MODIFIED Requirements

### Requirement: Django settings SHALL be importable at Docker build time without runtime env vars

All `config()` calls at module scope in `config/settings.py` MUST have a `default=` value that is
non-empty and satisfies any downstream truthy validation. This allows `RUN python manage.py
collectstatic` to succeed during the Docker image build, where runtime env vars injected via
`docker-compose.yml` are not present.

The `collectstatic` step in `Dockerfile` MUST be invoked with `DEBUG=True` so that the
production-mode placeholder-domain guard (see `Requirement: Production Startup Guard for
Placeholder SITE_DOMAIN`) is bypassed during the build stage.

#### Scenario: SITE_DOMAIN resolves at build time

- **Given** no `SITE_DOMAIN` env var is present in the Docker build container
- **And** the collectstatic command is run with `DEBUG=True`
- **When** Django imports `config/settings.py` during `collectstatic`
- **Then** `SITE_DOMAIN` resolves to `"localhost"` and no exception is raised

#### Scenario: CSRF_TRUSTED_ORIGINS resolves at build time

- **Given** no `CSRF_TRUSTED_ORIGINS` env var is present in the Docker build container
- **When** Django imports `config/settings.py` during `collectstatic`
- **Then** `CSRF_TRUSTED_ORIGINS` resolves to `["http://localhost"]` and no exception is raised

#### Scenario: Validation guard passes during build

- **Given** `ALLOWED_HOSTS` defaults to `"localhost,127.0.0.1"`, `SITE_DOMAIN` defaults to
  `"localhost"`, and `CSRF_TRUSTED_ORIGINS` defaults to `"http://localhost"`
- **And** `DEBUG=True` is set for the build command
- **When** the validation block in `settings.py` is evaluated
- **Then** no `ImproperlyConfigured` exception is raised

#### Scenario: Production values override defaults at runtime

- **Given** Coolify injects `SITE_DOMAIN` and `CSRF_TRUSTED_ORIGINS` as runtime env vars
- **When** the container starts in production
- **Then** the real domain values take effect, overriding the build-time defaults

## ADDED Requirements

### Requirement: Production Startup Guard for Placeholder SITE_DOMAIN

When `DEBUG=False`, `config/settings.py` MUST raise `django.core.exceptions.ImproperlyConfigured`
during module import if `SITE_DOMAIN` resolves to a known local placeholder hostname
(`"localhost"` or `"127.0.0.1"`). The check MUST strip any port suffix before comparing (e.g.
`"localhost:8000"` is still a placeholder). The error message MUST include the resolved value and
instruct the operator to set the correct production FQDN.

This guard MUST NOT fire when `DEBUG=True`, preserving the local-development workflow where
`SITE_DOMAIN=fastjob.localhost:8000` is the norm.

#### Scenario: Production startup with missing SITE_DOMAIN fails immediately

- **Given** a container starts with `DEBUG=False` and `SITE_DOMAIN` resolving to `"localhost"` (the python-decouple default when the env var is absent or empty)
- **When** Django imports `config/settings.py`
- **Then** `ImproperlyConfigured` is raised before any request is handled
- **And** the error message names the resolved value and instructs the operator to set `SITE_DOMAIN`

#### Scenario: Production startup with correct SITE_DOMAIN passes

- **Given** a container starts with `DEBUG=False` and `SITE_DOMAIN=fastjob.apps.darideveloper.com`
- **When** Django imports `config/settings.py`
- **Then** no `ImproperlyConfigured` exception is raised from the placeholder guard

#### Scenario: Local dev with DEBUG=True and localhost domain is exempt

- **Given** a developer runs the app locally with `DEBUG=True` and `SITE_DOMAIN=fastjob.localhost:8000`
- **When** Django imports `config/settings.py`
- **Then** no `ImproperlyConfigured` exception is raised
- **And** the placeholder guard is entirely skipped
