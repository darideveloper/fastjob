# Infrastructure Spec Delta — fix-build-time-settings-defaults

## ADDED Requirements

### Requirement: Django settings SHALL be importable at Docker build time without runtime env vars

All `config()` calls at module scope in `config/settings.py` MUST have a `default=` value that is
non-empty and satisfies any downstream truthy validation. This allows `RUN python manage.py
collectstatic` to succeed during the Docker image build, where runtime env vars injected via
`docker-compose.yml` are not present.

#### Scenario: SITE_DOMAIN resolves at build time

- **Given** no `SITE_DOMAIN` env var is present in the Docker build container
- **When** Django imports `config/settings.py` during `collectstatic`
- **Then** `SITE_DOMAIN` resolves to `"localhost"` and no exception is raised

#### Scenario: CSRF_TRUSTED_ORIGINS resolves at build time

- **Given** no `CSRF_TRUSTED_ORIGINS` env var is present in the Docker build container
- **When** Django imports `config/settings.py` during `collectstatic`
- **Then** `CSRF_TRUSTED_ORIGINS` resolves to `["http://localhost"]` and no exception is raised

#### Scenario: Validation guard passes during build

- **Given** `ALLOWED_HOSTS` defaults to `"localhost,127.0.0.1"`, `SITE_DOMAIN` defaults to
  `"localhost"`, and `CSRF_TRUSTED_ORIGINS` defaults to `"http://localhost"`
- **When** the validation block at `settings.py:344` is evaluated
- **Then** no `ImproperlyConfigured` exception is raised

#### Scenario: Production values override defaults at runtime

- **Given** Coolify injects `SITE_DOMAIN` and `CSRF_TRUSTED_ORIGINS` as runtime env vars
- **When** the container starts in production
- **Then** the real domain values take effect, overriding the build-time defaults

### Requirement: Production deployment MUST include SITE_DOMAIN and CSRF_TRUSTED_ORIGINS

The Coolify environment variable configuration for the `web` service SHALL include both
`SITE_DOMAIN` and `CSRF_TRUSTED_ORIGINS` with the correct production domain values.

#### Scenario: SITE_DOMAIN set in Coolify

- **Given** the Coolify env vars panel for the fastjob application
- **When** the deployment runs
- **Then** `SITE_DOMAIN` is set to the production FQDN (e.g. `fastjob.apps.darideveloper.com`)

#### Scenario: CSRF_TRUSTED_ORIGINS set in Coolify

- **Given** the Coolify env vars panel for the fastjob application
- **When** the deployment runs
- **Then** `CSRF_TRUSTED_ORIGINS` is set to the full HTTPS origin
  (e.g. `https://fastjob.apps.darideveloper.com`)
