## 1. Settings guard

- [x] 1.1 In `config/settings.py`, after the existing falsy-value guard (line 363), add a `_PLACEHOLDER_DOMAINS` set containing `"localhost"` and `"127.0.0.1"` and raise `ImproperlyConfigured` when `not DEBUG` and `SITE_DOMAIN.split(":")[0]` is in that set.

## 2. Dockerfile

- [x] 2.1 In `Dockerfile:30`, prepend `DEBUG=True` to the collectstatic command so the new guard is skipped during the Docker image build: `RUN DEBUG=True python manage.py collectstatic --noinput`.

## 3. Tests

- [x] 3.1 In `apps/mailing/tests/test_url_scheme.py`, add a test that overrides `settings.DEBUG=False` and `settings.SITE_DOMAIN="localhost"` and asserts `ImproperlyConfigured` is raised when `settings.py`'s guard logic is exercised (e.g. by calling a helper that re-runs the guard, or by using `override_settings` in a way that triggers it).
- [x] 3.2 Add a complementary test that sets `DEBUG=True` with `SITE_DOMAIN="localhost"` and asserts no exception is raised (dev-mode exemption).

## 4. Validation

- [x] 4.1 Run `openspec validate harden-site-domain-validation --strict` and confirm zero issues.
- [x] 4.2 Run the full test suite (`pytest apps/mailing/tests/test_url_scheme.py -v`) and confirm all tests pass.
- [x] 4.3 Smoke-test the Docker build locally (`docker build .`) to confirm `collectstatic` still succeeds.
