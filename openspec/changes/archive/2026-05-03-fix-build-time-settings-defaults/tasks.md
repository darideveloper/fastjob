# Tasks: fix-build-time-settings-defaults

Ordered list of verifiable work items.

## Implementation

- [x] 1. `config/settings.py:107` — add `default="localhost"` to `SITE_DOMAIN` config call
- [x] 2. `config/settings.py:341` — add `default="http://localhost"` to `CSRF_TRUSTED_ORIGINS` config call

## Coolify configuration (manual)

- [ ] 3. Add `SITE_DOMAIN=fastjob.apps.darideveloper.com` in Coolify env vars
- [ ] 4. Add `CSRF_TRUSTED_ORIGINS=https://fastjob.apps.darideveloper.com` in Coolify env vars

## Verification

- [x] 5. Pushed to `main` (commit bf4db66)
- [ ] 6. Confirm build completes — `collectstatic` step must succeed without `UndefinedValueError`
- [ ] 7. Confirm running container responds to `GET /healthz` with HTTP 200

## Dependencies

- Tasks 1–2 must be complete before triggering the deploy (task 5)
- Tasks 3–4 must be complete in Coolify before the container starts (runtime)
- Tasks 1–2 are independent and can be done in a single commit
