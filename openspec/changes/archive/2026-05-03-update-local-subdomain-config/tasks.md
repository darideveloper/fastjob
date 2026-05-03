# Tasks: Update Local Subdomain Configuration

- [x] Remove hardcoded defaults from `config/settings.py` <!-- id: 0 -->
    - [x] Remove default for `ALLOWED_HOSTS`.
    - [x] Remove default for `CSRF_TRUSTED_ORIGINS`.
    - [x] Remove default for `SITE_DOMAIN`.
- [x] Update `.env.example` template <!-- id: 1 -->
    - [x] Update `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` examples.
- [x] Update active `.env` file <!-- id: 2 -->
    - [x] Update `ALLOWED_HOSTS` to include `fastjob.localhost`.
    - [x] Update `CSRF_TRUSTED_ORIGINS` to include `https://fastjob.localhost`.
- [x] Update documentation <!-- id: 3 -->
    - [x] Update `docs/local-subdomain-setup.md` to mention `fastjob.localhost`.
- [x] Validation <!-- id: 4 -->
    - [x] Verify settings via `python manage.py diffsettings`.
    - [x] Verify that the application raises `ImproperlyConfigured` when essential environment variables (`ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `SITE_DOMAIN`) are missing.
    - [x] (Optional/Manual) Verify access via `curl -H "Host: fastjob.localhost" http://localhost:8000`.
