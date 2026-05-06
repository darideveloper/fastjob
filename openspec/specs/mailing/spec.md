# mailing Specification

## Purpose
TBD - created by archiving change add-company-filter-finder. Update Purpose after archive.
## Requirements
### Requirement: Mailing Engine Token Refresh
The mailing engine MUST use credentials from the `SocialApp` database model for all OAuth2 token refresh operations. This ensures that credential updates in the database take immediate effect for background tasks.

#### Scenario: Token refresh retrieves credentials from DB
- **GIVEN** a valid `SocialApp` record exists for the provider (e.g., 'google') with correct `client_id` and `secret`.
- **AND** a user's `SocialToken` is expired.
- **WHEN** the mailing engine attempts to refresh the token.
- **THEN** it MUST query the `SocialApp` table for the provider's credentials.
- **AND** use those credentials in the POST request to the provider's token endpoint.
- **AND** the refresh succeeds if the credentials match the provider's records.

#### Scenario: Missing SocialApp record raises error
- **GIVEN** no `SocialApp` record exists for a linked provider.
- **WHEN** the mailing engine attempts a token refresh.
- **THEN** it MUST raise a `TokenExpiredError` (or similar) indicating that the OAuth configuration is missing.
- **AND** the error message MUST specify the missing provider.

### Requirement: One-Time Normalization of Existing User Filters
On deployment of the exact-match semantics, a forward-only data migration SHALL normalize every existing user's `area_filter` and `location_filter`. Any value that does not appear (case-insensitively, after stripping whitespace) in the current `Company.area` / `Company.location` distinct set MUST be cleared to the empty string. Values that do appear MUST be preserved unchanged.

#### Scenario: Stale free-text filter is cleared
- **GIVEN** a user has `area_filter = "ghost-sector"` from the previous free-text era
- **AND** no `Company` row has `area` equal (case-insensitively) to `"ghost-sector"`
- **WHEN** the data migration runs
- **THEN** the user's `area_filter` is set to `""`

#### Scenario: Valid filter survives the migration
- **GIVEN** a user has `area_filter = "Tecnología"`
- **AND** at least one `Company` row has `area = "Tecnología"` (case-insensitively)
- **WHEN** the data migration runs
- **THEN** the user's `area_filter` remains `"Tecnología"`

#### Scenario: Migration is forward-only
- **WHEN** the migration's reverse operation is invoked
- **THEN** the operation is a no-op (cleared filters are NOT restored, since the previous behavior also matched zero rows for those values)

### Requirement: Persist Rotated OAuth Refresh Tokens

The mailing engine's refresh helpers (`_refresh_google_token` and `_refresh_microsoft_token` in `apps/mailing/engine.py`) MUST persist a rotated `refresh_token` to `SocialToken.token_secret` whenever the provider's token-endpoint response includes a `refresh_token` field. The save MUST include `"token_secret"` in the `update_fields` list for that case. When the response omits `refresh_token`, the existing `token_secret` MUST be left unchanged. The refresh-and-save sequence MUST execute inside a transaction with `select_for_update()` on the `SocialToken` row to prevent two concurrent refreshes from racing.

#### Scenario: Microsoft refresh response with rotated refresh token is persisted

- **GIVEN** a user with a linked Microsoft account whose `SocialToken.token_secret` is `"old-refresh-abc"`
- **WHEN** the engine calls `_refresh_microsoft_token` and the Microsoft token endpoint returns `{"access_token": "new-access", "refresh_token": "new-refresh-xyz", "expires_in": 3600}`
- **THEN** `SocialToken.token` is updated to `"new-access"`
- **AND** `SocialToken.token_secret` is updated to `"new-refresh-xyz"`
- **AND** the `update_fields` argument passed to `.save()` includes both `"token"` and `"token_secret"`

#### Scenario: Google refresh response without a refresh token preserves the existing one

- **GIVEN** a user with a linked Google account whose `SocialToken.token_secret` is `"google-refresh-keep"`
- **WHEN** the engine calls `_refresh_google_token` and the Google token endpoint returns `{"access_token": "new-access", "expires_in": 3600}` (no `refresh_token` key)
- **THEN** `SocialToken.token_secret` is still `"google-refresh-keep"` after the save
- **AND** the `update_fields` argument passed to `.save()` does NOT include `"token_secret"`

#### Scenario: Concurrent refreshes for the same user are serialized

- **GIVEN** two Celery workers attempt to refresh the same `SocialToken` row at the same instant, both finding `expires_at` in the past
- **WHEN** both refresh helpers run
- **THEN** the second worker waits on the row lock acquired by the first
- **AND** when the second worker proceeds, its pre-save expiration check sees the freshly written value and short-circuits without issuing a duplicate HTTP refresh call

### Requirement: Transient Refresh Failures Do Not Pause Campaigns

The mailing engine MUST distinguish transient OAuth refresh failures (HTTP 5xx, HTTP 429, network timeouts, connection errors) from terminal failures (HTTP 401/403, HTTP 400 with `error in {invalid_grant, invalid_client, unauthorized_client}`, and unrecognized failures). Transient failures MUST raise `TokenRefreshTransientError`, and `process_mailing_queue` MUST handle that exception by marking the per-attempt `MailingLog` row as `FAILED` while leaving `User.is_campaign_active = True` and NOT enqueuing `send_relink_notification`. Terminal failures MUST continue to raise `TokenExpiredError` and trigger the existing pause-and-notify flow.

#### Scenario: Google token endpoint returns HTTP 503 — campaign stays active

- **GIVEN** an active user whose access token has expired
- **AND** Google's token endpoint returns HTTP 503 with body `{"error": "backendError"}`
- **WHEN** `process_mailing_queue` attempts to send for that user
- **THEN** `_refresh_google_token` raises `TokenRefreshTransientError`
- **AND** the user's `MailingLog` row for this attempt is marked `FAILED` with the error message recorded
- **AND** `User.is_campaign_active` remains `True`
- **AND** `send_relink_notification.delay(user.pk)` is NOT called

#### Scenario: Microsoft token endpoint returns HTTP 400 invalid_grant — campaign pauses

- **GIVEN** an active user whose Microsoft refresh token was revoked from the Microsoft security panel
- **AND** Microsoft's token endpoint returns HTTP 400 with body `{"error": "invalid_grant"}`
- **WHEN** `process_mailing_queue` attempts to send for that user
- **THEN** `_refresh_microsoft_token` raises `TokenExpiredError`
- **AND** `User.is_campaign_active` is set to `False`
- **AND** `send_relink_notification.delay(user.pk)` is enqueued

#### Scenario: Network timeout during refresh — campaign stays active

- **GIVEN** an active user whose access token has expired
- **AND** the HTTP call to the provider's token endpoint raises `requests.Timeout`
- **WHEN** `process_mailing_queue` attempts to send for that user
- **THEN** `_refresh_<provider>_token` raises `TokenRefreshTransientError`
- **AND** `User.is_campaign_active` remains `True`
- **AND** the next scheduled beat tick will retry the user normally

#### Scenario: HTTP 429 from provider — campaign stays active

- **GIVEN** the provider returns HTTP 429 (rate limited)
- **WHEN** the refresh helper handles the response
- **THEN** it raises `TokenRefreshTransientError`
- **AND** the user's campaign is not paused

### Requirement: Deterministic Multi-Provider Account Selection

When a user has more than one linked `SocialAccount` (e.g., both Google and Microsoft), the mailing engine's `_get_social_token` MUST select the most recently linked account by ordering `SocialAccount` rows by `date_joined` descending and choosing the first. For the chosen account, the engine MUST select the most recently issued `SocialToken` by ordering its tokens by `id` descending and choosing the first. Selection MUST never depend on database row insertion order or unspecified default ordering.

#### Scenario: User with both Google and Microsoft uses the most recently linked one

- **GIVEN** a user has linked Google with `SocialAccount.date_joined = 2026-01-01`
- **AND** the same user later linked Microsoft with `SocialAccount.date_joined = 2026-04-15`
- **WHEN** `_get_social_token(user)` is called
- **THEN** the returned `(provider, social, token)` tuple has `provider == "microsoft"`

#### Scenario: User has multiple SocialToken rows for one provider — newest wins

- **GIVEN** a single Google `SocialAccount` with two `SocialToken` rows, ids `7` and `19`, where row `19` was written by the most recent refresh
- **WHEN** `_get_social_token(user)` is called
- **THEN** the returned `token` is the row with `id == 19`

### Requirement: OAuth Configuration Healthcheck and Fail-Loud Deploys

The deployment configuration MUST surface OAuth-related misconfigurations through the existing `/healthz/` endpoint and a new `manage.py check_oauth_config` management command. Specifically: a `GOOGLE_OAUTH_PROJECT_MODE` environment variable (default `"production"`) declares whether the Google OAuth consent screen is in Production or Testing mode, and `MICROSOFT_TENANT` (default `"common"`) declares the Microsoft tenant used in the token endpoint URL. The healthcheck MUST emit a warning when `GOOGLE_OAUTH_PROJECT_MODE == "testing"` because the 7-day refresh-token expiry window will silently break long-running campaigns. The management command MUST exit non-zero if the configured Microsoft tenant's OpenID discovery document is unreachable.

#### Scenario: Healthcheck warns when Google project is in Testing mode

- **GIVEN** the environment is started with `GOOGLE_OAUTH_PROJECT_MODE=testing`
- **WHEN** an HTTP client requests `/healthz/`
- **THEN** the response body indicates a warning state for the OAuth-config check, naming `GOOGLE_OAUTH_PROJECT_MODE` as the cause
- **AND** a structured log line is emitted with the warning

#### Scenario: Healthcheck is silent when Google project is in Production

- **GIVEN** the environment is started with `GOOGLE_OAUTH_PROJECT_MODE=production` (or unset)
- **WHEN** an HTTP client requests `/healthz/`
- **THEN** the OAuth-config check reports OK with no warning

#### Scenario: check_oauth_config command fails when Microsoft tenant is misconfigured

- **GIVEN** `MICROSOFT_TENANT` is set to a value whose OpenID discovery URL (`https://login.microsoftonline.com/<tenant>/v2.0/.well-known/openid-configuration`) returns a non-2xx status
- **WHEN** an operator runs `python manage.py check_oauth_config`
- **THEN** the command writes a descriptive error to stderr and exits with a non-zero status code

### Requirement: Structured Logging of Every OAuth Refresh Outcome

Each invocation of `_refresh_google_token` and `_refresh_microsoft_token` MUST emit exactly one structured log record at INFO level with the following fields in the `extra` dict: `provider` (`"google"` or `"microsoft"`), `user_pk` (integer), `outcome` (one of `"hit_cache"`, `"refreshed"`, `"rotated"`, `"transient_error"`, `"terminal_error"`), `latency_ms` (integer, time spent on the HTTP call or 0 for cache hits), and `rotated` (boolean — true only when the response carried a new `refresh_token`). The log record MUST NOT include the access token value or the refresh token value, in either the message body or the `extra` dict.

#### Scenario: Successful Microsoft refresh with rotation logs outcome=rotated

- **GIVEN** a Microsoft refresh completes successfully and the response includes a new `refresh_token`
- **WHEN** `_refresh_microsoft_token` returns
- **THEN** exactly one log record is written with `extra={"provider": "microsoft", "user_pk": <int>, "outcome": "rotated", "latency_ms": <int>, "rotated": true}`

#### Scenario: Cache hit logs outcome=hit_cache with zero latency

- **GIVEN** an access token whose `expires_at` is more than 60 seconds in the future
- **WHEN** the refresh helper is called
- **THEN** no HTTP request is made
- **AND** exactly one log record is written with `extra={"provider": ..., "user_pk": ..., "outcome": "hit_cache", "latency_ms": 0, "rotated": false}`

#### Scenario: Refresh failure logs outcome and never logs the token

- **GIVEN** a refresh that raises `TokenRefreshTransientError` or `TokenExpiredError`
- **WHEN** the helper exits
- **THEN** the emitted log record's `extra["outcome"]` is `"transient_error"` or `"terminal_error"` respectively
- **AND** neither the log message nor any `extra` value contains the access token or the refresh token string

### Requirement: Daily Email Limit per User
The mailing engine MUST respect a global `max_emails_per_day_per_user` setting (configured via the `SystemSettings` singleton). For any given user, the number of emails sent (measured by `MailingLog` entries with `status=SENT`) within the trailing 24-hour window MUST NOT exceed this limit. When a user hits this limit, the `process_mailing_queue` task MUST skip them until the rolling 24-hour window allows more sends.

#### Scenario: User is skipped when daily limit is reached
- **GIVEN** `SystemSettings.max_emails_per_day_per_user` is set to 50
- **AND** a user has 50 `MailingLog` entries with `status="sent"` in the last 24 hours
- **WHEN** `process_mailing_queue` evaluates the user
- **THEN** the user is skipped for this tick
- **AND** no email is sent
- **AND** their `credits_remaining` is not decremented

#### Scenario: User receives email when below daily limit
- **GIVEN** `SystemSettings.max_emails_per_day_per_user` is set to 50
- **AND** a user has 49 `MailingLog` entries with `status="sent"` in the last 24 hours
- **WHEN** `process_mailing_queue` evaluates the user (and all other cooldown/interval conditions are met)
- **THEN** the engine sends an email to the next eligible company
- **AND** a new `MailingLog` entry is created

