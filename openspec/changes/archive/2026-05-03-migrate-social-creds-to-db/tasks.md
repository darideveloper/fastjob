# Tasks: Migrate Social Credentials to Database

## 1. Preparation & Configuration
- [x] Ensure `SITE_ID` is correctly set in `config/settings.py` and a `Site` object exists for the current domain.
- [x] Verify `django.contrib.sites` and `allauth.socialaccount` are in `INSTALLED_APPS`.

## 2. Data Migration
- [x] Create a custom Django management command `apps/accounts/management/commands/sync_social_creds.py` to migrate credentials from `settings` to `SocialApp` records.
    - This command should handle missing `Site` objects and provide idempotent updates.
- [x] Execute the management command and verify `SocialApp` records are created in the database.

## 3. Refactor Mailing Engine
- [x] Modify `apps/mailing/engine.py` to fetch credentials from `SocialApp` instead of `settings.SOCIALACCOUNT_PROVIDERS`.
- [x] Implement a helper function `_get_social_app(provider)` in `apps/mailing/engine.py` to encapsulate the lookup logic.
- [x] Ensure `_refresh_google_token` and `_refresh_microsoft_token` use the `SocialApp` credentials.

## 4. Update Configuration & Documentation
- [x] Remove `APP` dictionaries from `SOCIALACCOUNT_PROVIDERS` in `config/settings.py`.
- [x] Update `.env.example` to remove `GOOGLE_CLIENT_ID`, etc., or mark them as legacy, pointing to the Django Admin as the new source of truth.
- [x] Remove OAuth environment variables (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET`) from `docker-compose.yml`.
- [x] Update documentation files (`README.md`, `docs/deploy.md`, `docs/run.md`, `docs/features/authentication.md`, `docs/features/mailing-engine.md`) to reflect that social credentials are now configured via the Django Admin (SocialApp model) instead of `.env`.

## 5. Validation
- [x] Test Google Login flow (end-to-end).
- [x] Test Microsoft Login flow (end-to-end).
- [x] Run `pytest apps/mailing/tests/` to ensure background token refresh still works.
- [x] Update `apps/mailing/tests/test_engine.py` to mock `SocialApp` instead of relying on `settings.SOCIALACCOUNT_PROVIDERS`.
- [x] Manually verify that updating a secret in Django Admin takes effect without a restart.
