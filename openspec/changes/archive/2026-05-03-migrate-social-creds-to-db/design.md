# Design: Credential Migration to SocialApp

## Architecture
The migration shifts the source of truth for OAuth credentials from static settings to dynamic database records.

### Current Flow
1.  `.env` contains `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, etc.
2.  `config/settings.py` populates `SOCIALACCOUNT_PROVIDERS` with an `APP` key.
3.  `allauth` and `apps/mailing/engine.py` read from `settings.SOCIALACCOUNT_PROVIDERS`.

### New Flow
1.  The database `SocialApp` table contains the credentials.
2.  `config/settings.py` defines `SOCIALACCOUNT_PROVIDERS` *without* the `APP` key.
3.  `allauth` automatically searches the `SocialApp` table when `APP` is missing from settings.
4.  `apps/mailing/engine.py` is refactored to query `SocialApp` for the credentials needed for token refresh.

## Component Changes

### 1. Configuration (`config/settings.py`)
Remove the `APP` dictionary for each provider. The `SCOPE` and `AUTH_PARAMS` will remain in `settings.py` as they define application behavior rather than identity.

### 2. Mailing Engine (`apps/mailing/engine.py`)
Refactor `_refresh_google_token` and `_refresh_microsoft_token` to use a new internal helper `_get_social_app(provider)`.
This helper will:
- Query `SocialApp.objects.filter(provider=provider).first()`.
- Raise `TokenExpiredError` (or a more specific configuration error) if the app is missing, as this indicates a setup issue that prevents refresh.
- Return the `client_id` and `secret`.

### 3. Data Migration (Management Command)
Instead of a raw shell script, a management command `sync_social_creds` will be implemented. This ensures:
- Integration with standard deployment workflows.
- Better error handling (e.g., if the `Site` table is empty).
- Safe logging of progress.
- Idempotency: it can be run multiple times without creating duplicate records.

## Trade-offs
- **Security:** Credentials move from the environment to the database. While standard for many CMS-like systems, it expands the attack surface if the database is compromised. Database-level encryption or restricted Admin access should be considered.
- **Performance:** Adds a database query per token refresh. Given the low frequency and volume of refreshes, this is negligible.
