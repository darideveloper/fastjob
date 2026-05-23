# mailing Specification

## Purpose
The mailing engine is responsible for dispatching CV emails via OAuth2-linked providers (Gmail and Microsoft Graph), managing the OAuth token lifecycle, and enforcing global sending constraints such as slow-drip intervals, daily limits, and email visibility settings.
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

### Requirement: Two-Step Unsubscribe Flow
The `/unsubscribe/<uuid:token>/` endpoint MUST distinguish read-only access (browser fetches, scanner pre-fetch, manual link click) from the explicit opt-out action.
- A `GET` to the URL MUST NOT mutate any persistent state. It MUST render an interstitial confirmation page that includes a CSRF-stamped HTML form whose `action` posts back to the same URL.
- A `POST` to the URL MUST resolve the recipient email from `MailingLog.company_email_snapshot` (falling back to `MailingLog.company.email` if the snapshot is empty), MUST insert or refresh a `Blacklist` row keyed by the lowercased / stripped email via the `Blacklist.add(...)` helper, and MUST set `MailingLog.unsubscribed_at = timezone.now()` on the log row identified by the unsubscribe token **only on the first successful POST**. Subsequent replays against the same token MUST NOT overwrite the original `unsubscribed_at` value — the field captures the moment the recipient first opted out, not the moment of the latest replay.
- The `POST` handler MUST be exempt from Django's CSRF middleware. The unsubscribe token in the URL is the authentication factor.
- Both methods MUST share the existing per-IP rate limit (`10/h`).
- All email snapshots in `MailingLog` MUST be normalized to lowercase upon save to ensure consistency with the `Blacklist` and `Company` records.

#### Scenario: Email-client GET pre-fetch does not blacklist
- **GIVEN** an email recipient whose mail client (Outlook Safe Links, Gmail link scanner, corporate AV proxy) silently fetches every URL inside an incoming message
- **WHEN** the client issues `GET /unsubscribe/<valid-token>/`
- **THEN** the response is `200 OK` rendering the interstitial confirmation page
- **AND** no `Blacklist` row is created
- **AND** the corresponding `MailingLog.unsubscribed_at` remains `NULL`

#### Scenario: MailingLog snapshot is lowercased
- **WHEN** a `MailingLog` is created with `company_email_snapshot = "FOO@Empresa.ES"`
- **THEN** the field is saved as `"foo@empresa.es"`
- **AND** the unsubscribe lookup correctly matches it against the normalized `Blacklist`

#### Scenario: MailingLog without snapshot or company is invalid
- **WHEN** a `MailingLog` is saved with both `company` and `company_email_snapshot` empty
- **THEN** the system MUST raise a `ValidationError` during the `clean()` phase.

### Requirement: Outgoing Email MUST Carry List-Unsubscribe Headers

Every CV email sent by the mailing engine — via the Gmail send path AND via the Microsoft Graph send path — MUST include the following two headers in the outgoing message:
- `List-Unsubscribe: <{unsubscribe_url}>` where `{unsubscribe_url}` is the same fully-qualified URL placed in the email body's HTML link.
- `List-Unsubscribe-Post: List-Unsubscribe=One-Click` (RFC 8058).

The header values MUST NOT contain newline characters. The Gmail path MUST embed the headers in the raw RFC 822 message before base64url encoding. The Microsoft Graph path MUST emit the headers via the `internetMessageHeaders` field on the `sendMail` payload; if Graph rejects the unprefixed header names with HTTP 400, the engine MAY retry once with `x-list-unsubscribe` / `x-list-unsubscribe-post`. The fallback path MUST be gated by a process-level flag (a module-level boolean, or a small set keyed by tenant/provider) so that the WARNING log record is emitted at most once per process, regardless of how many sends subsequently take the fallback path. The WARNING record's `extra` dict MUST include `provider="microsoft"`, `status` (the rejected status code, typically 400), and `fallback="x-prefix"`; it MUST NOT include the recipient address, the access token, or the message body.

#### Scenario: Gmail path emits both headers

- **GIVEN** a user with a linked Google account is sending a CV
- **WHEN** `_send_via_gmail` posts the message to the Gmail API
- **THEN** the base64url-decoded MIME contains a `List-Unsubscribe` header whose URL equals `{SITE_SCHEME}://{SITE_DOMAIN}/unsubscribe/{log.unsubscribe_token}/`
- **AND** it contains the literal header `List-Unsubscribe-Post: List-Unsubscribe=One-Click`

#### Scenario: Microsoft Graph path emits both headers

- **GIVEN** a user with a linked Microsoft account is sending a CV
- **WHEN** `_send_via_microsoft` posts the message to the Graph `sendMail` endpoint
- **THEN** the JSON payload's `message.internetMessageHeaders` array contains an entry with `name == "List-Unsubscribe"` whose value is `<{unsubscribe_url}>`
- **AND** it contains an entry with `name == "List-Unsubscribe-Post"` whose value is `List-Unsubscribe=One-Click`

#### Scenario: Graph rejects unprefixed header — fallback emits prefixed names

- **GIVEN** a Microsoft tenant whose Graph endpoint returns HTTP 400 because the unprefixed `List-Unsubscribe` header is rejected
- **WHEN** `_send_via_microsoft` retries with prefixed names
- **THEN** the second request succeeds with `internetMessageHeaders` carrying `x-list-unsubscribe` and `x-list-unsubscribe-post`
- **AND** a WARNING-level structured log line is emitted at most once per process, with `extra={"provider": "microsoft", "status": 400, "fallback": "x-prefix"}`

#### Scenario: Repeated Graph fallbacks do NOT spam WARNING logs

- **GIVEN** a Microsoft tenant whose Graph endpoint persistently rejects the unprefixed header (so every send takes the fallback path)
- **WHEN** the engine sends N (N ≥ 2) consecutive CV emails through the fallback path within a single worker process
- **THEN** exactly one WARNING-level fallback log record is emitted across all N sends
- **AND** every send still succeeds end-to-end via the prefixed-header retry

### Requirement: Blacklist Gates the CV Download View

The `cv_download` view MUST refuse to generate a presigned S3 URL when the recipient's email is in `Blacklist`. The recipient email is resolved from `MailingLog.company_email_snapshot`, falling back to `MailingLog.company.email`.

#### Scenario: Opted-out recipient cannot download the CV

- **GIVEN** a `MailingLog` whose `company_email_snapshot` matches a row in `Blacklist`
- **WHEN** any client issues `GET /cv/<token>/` for that log
- **THEN** the response status is `410 Gone`
- **AND** the response body is the `cv_revoked.html` template
- **AND** no presigned S3 URL is generated and no S3 SDK call is made

#### Scenario: Active recipient still receives the presigned redirect

- **GIVEN** a `MailingLog` whose recipient is NOT in `Blacklist`
- **WHEN** the recipient issues `GET /cv/<token>/`
- **THEN** the response is `302 Found` with the `Location` header set to a presigned S3 URL
- **AND** the `Cache-Control` header is `no-store`

### Requirement: Structured Log Line on Successful Unsubscribe

Every successful `POST /unsubscribe/<token>/` that mutates state (i.e. the FIRST POST against a given log token) MUST emit exactly one structured log record at INFO level with the following fields in the `extra` dict: `outcome="unsubscribed"`, `user_pk` (integer, from the log's user), `template_id` (integer or null), `log_pk` (integer), `company_email_sha256` (the SHA-256 hex digest of the recipient email after the SAME normalization that `Blacklist.add` applies — namely `email.strip().lower()`). The log record MUST NOT include the recipient email in clear text and MUST NOT include the unsubscribe token.

The strip-then-lower normalization is normative (not advisory): downstream analytics that join the structured log against `Blacklist.email` expect the hash to match what they would compute from the canonical blacklist key. A producer that hashes the un-stripped value and a producer that hashes the stripped value would silently fail to join.

#### Scenario: One log record per successful POST

- **WHEN** a recipient successfully POSTs to the unsubscribe URL for the first time
- **THEN** exactly one log record is emitted at INFO level with the five fields above
- **AND** the record's message body and `extra` values do NOT contain the email in clear text or the unsubscribe token

#### Scenario: Hash matches the canonical Blacklist key normalization

- **GIVEN** an unsubscribe POST whose resolved recipient email contains leading or trailing whitespace (e.g. `"  Contact@Empresa.ES  "`)
- **WHEN** the structured `outcome="unsubscribed"` record is emitted
- **THEN** `extra["company_email_sha256"]` equals `sha256(b"contact@empresa.es").hexdigest()` — i.e. the hash of the **stripped** AND **lowercased** email
- **AND** the same hash equals what an analytics consumer would compute from the corresponding `Blacklist.email` row

#### Scenario: No log record on GET

- **WHEN** the unsubscribe URL is fetched via GET (interstitial render)
- **THEN** no `outcome="unsubscribed"` log record is emitted

### Requirement: Slow-Drip Campaign Engine Matching
The slow-drip mailing engine SHALL match a user's `area_filters` and `location_filters` against `Company.area` and `Company.location` using case-insensitive **exact** equality, not substring matching. An empty list MUST mean "no filter on that field". The engine MUST source its eligible-company queryset from the same shared helper used by the dashboard's live counter, so that the two cannot drift. To ensure scalability, exclusions (notably the `Blacklist` and recently contacted companies) MUST be applied using database-level subqueries (`NOT IN (SELECT ...)`) where possible. The engine MAY use a small in-memory set to track companies contacted within the current task execution tick to prevent duplicate sends across concurrent users.

#### Scenario: Filter fields determine eligibility via IN clause
- **GIVEN** a user with `area_filters = ["Tecnología", "Marketing"]`
- **WHEN** the slow-drip task runs for that user
- **THEN** only companies whose `area.name` exactly matches (case-insensitively) `"Tecnología"` or `"Marketing"` are considered for sending

#### Scenario: Blacklist exclusion uses a subquery
- **GIVEN** a large `Blacklist` table
- **WHEN** the engine filters companies
- **THEN** it generates a SQL `NOT IN (SELECT ...)` clause
- **AND** it does NOT load the full blacklist into memory or pass it as a parameter list to the query

### Requirement: CV PDF Attachments
The mailing engine MUST attach the user's active CV as a PDF file directly to the outgoing email message for both Google and Microsoft providers. The attachment MUST be correctly encoded (base64) and specify the `application/pdf` content type. The system MUST gracefully handle file read errors if the physical file is missing from storage.

#### Scenario: Gmail sends email with PDF attachment
- **GIVEN** a user has an active CV file
- **WHEN** `_send_via_gmail` is called
- **THEN** the message payload is formatted as a `multipart/mixed` MIME message
- **AND** it contains an `application/pdf` attachment part with the correct filename.

#### Scenario: Microsoft Graph sends email with PDF attachment
- **GIVEN** a user has an active CV file
- **WHEN** `_send_via_microsoft` is called
- **THEN** the JSON payload contains an `attachments` array
- **AND** the array includes an item of type `#microsoft.graph.fileAttachment` containing the base64-encoded PDF content.

#### Scenario: Missing physical CV file pauses campaign
- **GIVEN** a user's active CV record points to a file that does not exist in storage
- **WHEN** `send_cv_email` is called
- **THEN** a `FileNotFoundError` or `OSError` is caught
- **AND** the user's campaign is paused (`is_campaign_active = False`)
- **AND** an exception is raised so the Celery worker marks the log as failed.

### Requirement: Mailing Queue Concurrency Safety

The system MUST ensure that only one instance of the `process_mailing_queue` background task executes at any given time to prevent race conditions that bypass sending intervals and daily limits. This MUST be implemented using an atomic distributed lock via the application cache. If the lock cannot be acquired, the task MUST exit early without processing any emails. The lock MUST be released when the task finishes execution, and MUST have a timeout fallback to prevent deadlocks in case of worker failure.

#### Scenario: Concurrent task execution is blocked
- **GIVEN** an instance of `process_mailing_queue` is currently running and holding the lock
- **WHEN** a second instance of `process_mailing_queue` is triggered by Celery Beat
- **THEN** the second instance fails to acquire the lock
- **AND** it logs that it is skipping the tick
- **AND** it exits immediately without sending any emails or updating database state

#### Scenario: Lock is released after successful execution
- **GIVEN** an instance of `process_mailing_queue` successfully acquires the lock
- **WHEN** the task completes processing the queue
- **THEN** the lock is deleted from the cache
- **AND** subsequent task triggers are able to acquire the lock

#### Scenario: Lock is released after an exception
- **GIVEN** an instance of `process_mailing_queue` successfully acquires the lock
- **WHEN** an unhandled exception occurs during processing
- **THEN** the task ensures the lock is still deleted from the cache via a `finally` block before bubbling up the exception

### Requirement: Dynamic Initial Credits
The system SHALL allow the administrator to configure the number of free credits granted to new users upon signup. This value MUST be stored in the `SystemSettings` singleton as `initial_free_credits` and default to 5.

#### Scenario: New user receives dynamic signup bonus
- **GIVEN** `SystemSettings.initial_free_credits` is set to 10.
- **WHEN** a new user signs up and the `user_signed_up` signal fires.
- **THEN** the user's `credits_remaining` MUST be set to 10.
- **AND** `total_purchased_credits` MUST remain at 0.

### Requirement: Hidden Credit Multiplier
The mailing engine SHALL allow paid users to send a small margin of extra emails beyond their purchased balance, controlled by a global multiplier.
- The multiplier `hidden_credit_multiplier` (e.g., 1.1 for 10% extra) is stored in `SystemSettings` and defaults to 1.00.
- The multiplier MUST only apply to `total_purchased_credits`, not to free signup bonuses.
- The "Hidden Floor" is calculated as `ceil(user.total_purchased_credits * (multiplier - 1))`.
- A user is eligible to send if `user.credits_remaining > -hidden_floor`.
- The `User.can_send()` method MUST be updated to incorporate this hidden floor check.

#### Scenario: User with 1.1x multiplier sends beyond zero
- **GIVEN** a user has purchased 50 credits (`total_purchased_credits = 50`).
- **AND** the global `hidden_credit_multiplier` is `1.1`.
- **AND** the user's `credits_remaining` is `0`.
- **WHEN** the mailing engine evaluates the user via `can_send()`.
- **THEN** it MUST return `True` because `0 > -ceil(50 * 0.1)` (which is `0 > -5`).
- **AND** the engine sends the email and decrements `credits_remaining` to `-1`.

#### Scenario: User hits the hidden floor
- **GIVEN** a user has purchased 50 credits and the multiplier is `1.1` (floor is `-5`).
- **AND** the user's `credits_remaining` is `-5`.
- **WHEN** the mailing engine evaluates the user via `can_send()`.
- **THEN** it MUST return `False` because `-5` is not greater than `-5`.

#### Scenario: Multiplier of 1.0 does not grant extra credits
- **GIVEN** a user has purchased 100 credits and the multiplier is `1.0`.
- **AND** the user's `credits_remaining` is `0`.
- **WHEN** the mailing engine evaluates the user.
- **THEN** it MUST return `False` because the floor is 0.

### Requirement: OAuth Token Refresh Buffer
The engine MUST proactively refresh access tokens before they expire to accommodate clock skew and network latency.

#### Scenario: Token is near expiration
- **GIVEN** an access token stored in the database with an `expires_at` timestamp
- **WHEN** the engine evaluates the token and `expires_at` is less than 600 seconds (10 minutes) in the future
- **THEN** the engine MUST perform a proactive refresh before attempting to send.

### Requirement: Send-Time Error Classification
The engine MUST distinguish between terminal and transient errors during the email delivery phase (not just the refresh phase).

#### Scenario: Microsoft Graph returns 401 or 403
- **GIVEN** an active campaign attempting to send via Microsoft
- **WHEN** the `sendMail` endpoint returns HTTP 401 (Unauthorized) or 403 (Forbidden)
- **THEN** the engine MUST raise `TokenExpiredError`
- **AND** the mailing task MUST pause the campaign (`is_campaign_active = False`) and notify the user.

#### Scenario: Microsoft Graph returns 429 or 5xx
- **GIVEN** an active campaign attempting to send via Microsoft
- **WHEN** the `sendMail` endpoint returns HTTP 429 (Too Many Requests) or a 5xx server error
- **THEN** the engine MUST raise `TokenRefreshTransientError`
- **AND** the mailing task MUST mark the log as `FAILED` but leave the campaign active.

### Requirement: Failure-Aware Sending Intervals
The mailing engine MUST respect the global send interval regardless of the success or failure of previous attempts.

#### Scenario: Previous attempt failed
- **GIVEN** a user whose last mailing attempt at `T` resulted in a `FAILED` status
- **WHEN** the mailing task runs at `T + 1 minute`
- **AND** the `global_send_interval_minutes` is 5
- **THEN** the task MUST skip the user until `T + 5 minutes` has passed.

### Requirement: Email API Integration
The system MUST dispatch CV emails via the authenticated user's chosen provider using their native APIs (Gmail API for Google, Microsoft Graph API for Microsoft). The system MUST handle authentication state securely and appropriately for background task dispatch.

#### Scenario: Sending via Microsoft Graph with visibility off
- **WHEN** a CV email is dispatched via a linked Microsoft account AND the global visibility toggle is `False`
- **THEN** the system calls the `sendMail` endpoint with `saveToSentItems` set to `False`.

#### Scenario: Sending via Microsoft Graph with visibility on
- **WHEN** a CV email is dispatched via a linked Microsoft account AND the global visibility toggle is `True`
- **THEN** the system calls the `sendMail` endpoint with `saveToSentItems` set to `True`.

#### Scenario: Sending via Gmail API with visibility off
- **WHEN** a CV email is dispatched via a linked Google account AND the global visibility toggle is `False`
- **THEN** the system calls the `users.messages.send` endpoint, retrieves the message ID, and subsequently calls `users.messages.trash` or `users.messages.delete` to remove it from the Sent folder.

#### Scenario: Sending via Gmail API with visibility on
- **WHEN** a CV email is dispatched via a linked Google account AND the global visibility toggle is `True`
- **THEN** the system calls the `users.messages.send` endpoint and does not attempt to delete it.

### Requirement: Global Email Visibility Toggle
The system SHALL provide a global configuration toggle inside `SystemSettings`
(`/admin/mailing/systemsettings/1/change/`) to determine whether sent CV emails are
saved to the user's "Sent Items" folder. The toggle is stored as
`SystemSettings.save_emails_to_sent_folder` (Boolean, default `False`). The former
`SystemConfig` model in `apps.core` and its admin page at
`/admin/core/systemconfig/` are removed; `SystemSettings` is the single authoritative
source for all global mailing engine settings.

#### Scenario: Admin toggles visibility on
- **WHEN** an admin sets `save_emails_to_sent_folder` to `True` in
  `/admin/mailing/systemsettings/1/change/`
- **THEN** emails sent via both Microsoft and Google OAuth accounts are saved to all
  users' respective sent folders.

#### Scenario: Admin toggles visibility off
- **WHEN** an admin sets `save_emails_to_sent_folder` to `False` in
  `/admin/mailing/systemsettings/1/change/`
- **THEN** emails sent via Microsoft do not appear in the sent folder AND emails sent
  via Gmail are immediately deleted from the user's mailbox across all users.

#### Scenario: Existing configuration is preserved after migration
- **GIVEN** a live database where `core_systemconfig` pk=1 has
  `save_emails_to_sent_folder = True`
- **WHEN** the migrations `mailing 0011` and `core 0002` are applied
- **THEN** `mailing_systemsettings` pk=1 has `save_emails_to_sent_folder = True` and
  the `core_systemconfig` table no longer exists.

### Requirement: Campaign Pause Reason Persistence
The system MUST persist the specific reason why a campaign was automatically paused to provide accurate feedback to the user.

#### Scenario: Pause reason is saved on error
- **GIVEN** an active campaign
- **WHEN** the system pauses the campaign due to a terminal error (Quota or Expiry)
- **THEN** the `User.campaign_pause_reason` MUST be set to the corresponding reason (`quota` or `expired`).

#### Scenario: Pause reason is cleared on manual action
- **GIVEN** a user with a `campaign_pause_reason` set
- **WHEN** the user manually clicks "Iniciar campaña" or "Pausar campaña"
- **THEN** the `campaign_pause_reason` MUST be cleared (set to empty string).

### Requirement: Dashboard Warning Banner
The dashboard UI MUST display a clear explanation and call to action if the campaign was paused by the system.

#### Scenario: User sees Quota warning
- **GIVEN** a user with `campaign_pause_reason = "quota"`
- **WHEN** the user views their dashboard
- **THEN** a warning banner MUST be visible stating that the daily provider limit was reached.

### Requirement: Reasoned Campaign Pause Notifications
When a campaign is paused by the system due to a terminal error, the notification sent to the user MUST clearly state the reason for the pause.

#### Scenario: Email for Quota Reached
- **GIVEN** a campaign is paused because of a `QuotaExceededError`
- **THEN** the email sent MUST specify that the **provider-enforced** limit was reached and the user should wait until tomorrow.

### Requirement: Unauthenticated email-landing card chrome
The templates `mailing/cv_not_found.html`, `mailing/cv_revoked.html`, `mailing/unsubscribe.html`, and `mailing/unsubscribe_confirm.html` SHALL each render a single centered card on the `brand.bg` page background, using the shared card chrome (`bg-white border border-brand-muted rounded-2xl shadow-sm p-6 sm:p-8`), centered with `mx-auto`, capped at `max-w-md` below `lg` and `max-w-lg` at `lg`+. The FastJob logo (`<picture>` referencing `static/images/fastjob-logo.{webp,png}`, classes `h-12 w-auto`, the wrapper carrying `aspect-ratio: 1226 / 450`) SHALL appear above the card title.

Because these screens are reached from email links by visitors who arrived for a single transactional purpose, the rendered navbar MUST suppress all authenticated-only items (Panel, Comprar, Salir, envíos chip) **even when `user.is_authenticated`** — a visitor who happens to be logged in another tab should still see only the brand logo and (optionally) the anonymous "Iniciar sesión" / "Empezar gratis" links. Implementation MAY achieve this by introducing a `{% block navbar %}` override slot in `base.html` that these four templates blank out or replace with a minimal logo-only navbar, or by switching these templates to a new minimal base template — either is acceptable; the requirement is on the rendered output.

No behavior or routing requirement from the existing `mailing` spec is modified.

#### Scenario: Email-landing screen suppresses authenticated navigation
- **GIVEN** a visitor whose session is authenticated in another tab
- **WHEN** they follow an email link to `/cv/<invalid-token>/` and `mailing/cv_not_found.html` renders
- **THEN** the rendered HTML contains the FastJob logo
- **AND** the rendered HTML does NOT contain a link to `/dashboard/`, `/payments/paquetes/`, `/accounts/logout/`, or the envíos chip
- **AND** the visitor's authenticated session is NOT invalidated by viewing this page (no logout side-effect)

#### Scenario: All four mailing email-landing screens share the card chrome
- **WHEN** each of `mailing/cv_not_found.html`, `mailing/cv_revoked.html`, `mailing/unsubscribe.html`, and `mailing/unsubscribe_confirm.html` is rendered
- **THEN** each page renders a single centered card whose classes resolve to `bg-white`, `border-brand-muted`, `rounded-2xl`, `shadow-sm`
- **AND** each renders the FastJob logo above the title with `h-12 w-auto`

### Requirement: Unsubscribe confirm-prompt CTA is brand-primary, not red
The "Confirmar baja" button on `mailing/unsubscribe_confirm.html` (the GET prompt page rendered by `apps/mailing/views.py:97`) SHALL use the primary-fill button variant (`bg-brand text-white hover:bg-brand-dark`) — NOT a destructive red variant (the current `bg-red-600 hover:bg-red-700` at `unsubscribe_confirm.html:18` MUST be replaced). The intent is to make the unsubscribe action clear and trustworthy rather than adversarial; semantic red is reserved for true destructive intent (e.g. delete account). The masked email being unsubscribed SHALL be rendered in `text-brand-ink font-semibold` so the visitor can clearly confirm which address is being removed. No behavior change to the unsubscribe POST handler is introduced.

#### Scenario: Unsubscribe-prompt button uses primary-fill, not red
- **GIVEN** a visitor following an unsubscribe email link
- **WHEN** `mailing/unsubscribe_confirm.html` is rendered for a valid token (GET)
- **THEN** the `Confirmar baja` `<button type="submit">` has classes resolving to `brand.DEFAULT` background and `brand.dark` hover
- **AND** no element on the page uses `bg-red-*` or `text-red-*` utility classes
- **AND** the masked email rendered at `unsubscribe_confirm.html:13` is shown in `brand.ink` with `font-semibold`

### Requirement: Unsubscribe result page provides a "Volver a FastJob" CTA
`mailing/unsubscribe.html` (the POST result page rendered by `apps/mailing/views.py:119`) SHALL retain its existing confirmation copy `Has cancelado la suscripción` and SHALL add a single ghost-style CTA labelled `Volver a FastJob` linking to `/`. The page currently has no CTA; visitors who finish the unsubscribe flow today reach a dead-end card. The new CTA gives them a graceful exit without re-engaging them in marketing or campaign flows.

#### Scenario: Unsubscribe result page offers a return link
- **GIVEN** a visitor who just submitted the unsubscribe confirmation
- **WHEN** `mailing/unsubscribe.html` renders the POST result
- **THEN** the rendered HTML contains the existing heading `Has cancelado la suscripción`
- **AND** a single `<a href="/">` link labelled `Volver a FastJob` is present, styled as a ghost button (`text-brand-dark hover:bg-brand-muted`)
- **AND** the success affordance is conveyed via `brand.dark` / `brand.DEFAULT`, not exclusively via `text-green-*`

### Requirement: Spanish verbose names on SystemSettings fields
All fields of `SystemSettings` (`apps/mailing/models.py`) SHALL declare an
explicit `verbose_name` in Spanish so Django admin displays readable Spanish
labels instead of auto-generated English title-case identifiers.

| Field | verbose_name |
|---|---|
| `global_send_interval_minutes` | `"Intervalo de envío (minutos)"` |
| `company_cooldown_hours` | `"Enfriamiento por empresa (horas)"` |
| `max_emails_per_day_per_user` | `"Máximo de envíos por usuario al día"` |
| `initial_free_credits` | `"Envíos gratuitos iniciales"` |
| `hidden_credit_multiplier` | `"Multiplicador oculto de envíos"` |

#### Scenario: SystemSettings change form shows Spanish labels
- **WHEN** a staff user opens `/admin/mailing/systemsettings/1/change/`
- **THEN** each field label is the Spanish string from the table above
- **AND** no English auto-generated label (e.g. "Global send interval minutes") is visible

### Requirement: Spanish verbose names on EmailTemplate fields
All fields of `EmailTemplate` (`apps/mailing/models.py`) SHALL declare an
explicit `verbose_name` in Spanish.

| Field | verbose_name |
|---|---|
| `name` | `"Nombre"` |
| `subject` | `"Asunto"` |
| `body_html` | `"Cuerpo HTML"` |
| `is_active` | `"Activa"` |
| `created_at` | `"Creada el"` |

#### Scenario: EmailTemplate change form shows Spanish labels
- **WHEN** a staff user opens `/admin/mailing/emailtemplate/<id>/change/`
- **THEN** each field label matches the Spanish string from the table above

### Requirement: Spanish verbose names on MailingLog fields
All fields of `MailingLog` (`apps/mailing/models.py`) SHALL declare an
explicit `verbose_name` in Spanish.

| Field | verbose_name |
|---|---|
| `user` | `"Usuario"` |
| `company` | `"Empresa"` |
| `email_template` | `"Plantilla de email"` |
| `cv` | `"CV"` |
| `cv_download_token` | `"Token de descarga del CV"` |
| `unsubscribe_token` | `"Token de baja"` |
| `sent_at` | `"Enviado el"` |
| `status` | `"Estado"` |
| `error_message` | `"Mensaje de error"` |
| `company_email_snapshot` | `"Email de la empresa"` |
| `unsubscribed_at` | `"Fecha de baja"` |

#### Scenario: MailingLog change form shows Spanish labels
- **WHEN** a staff user opens `/admin/mailing/mailinglog/<id>/change/`
- **THEN** each field label matches the Spanish string from the table above

### Requirement: SystemSettingsAdmin fieldset descriptions are pure Spanish prose
`SystemSettingsAdmin` (`apps/mailing/admin.py`) SHALL NOT expose raw Python identifier names in its fieldset `description` strings. Both descriptions MUST be rewritten as fully Spanish prose that explains the effect of the fields without referencing their Python names.

#### Scenario: Fieldset description contains no Python identifiers
- **WHEN** a staff user opens `/admin/mailing/systemsettings/1/change/`
- **THEN** neither fieldset description contains a string matching
  `global_send_interval_minutes`, `company_cooldown_hours`,
  `max_emails_per_day_per_user`, `initial_free_credits`,
  or `hidden_credit_multiplier`
- **AND** both descriptions are written entirely in Spanish

### Requirement: EmailTemplate admin preview column label is Spanish
`EmailTemplateAdmin` (`apps/mailing/admin.py`) SHALL set `preview_link.short_description` to `"Vista previa"` instead of the English `"Preview"`.

#### Scenario: EmailTemplate changelist column header reads "Vista previa"
- **WHEN** a staff user opens `/admin/mailing/emailtemplate/`
- **THEN** the column header for the preview link reads `"Vista previa"`
- **AND** the previous English header `"Preview"` is not visible

### Requirement: Company Name Rendered in Uppercase
`EmailTemplate.render()` SHALL uppercase the `company_name` argument before substituting it into `{company_name}` placeholders in both the subject and the HTML body, so every outgoing CV-campaign email displays the company name in all-caps regardless of the casing stored in the database.

The transformation MUST be applied in the Python render layer — not inside stored template markup — so that templates remain plain and no database migration is required.

#### Scenario: Mixed-case company name is uppercased in subject
- **GIVEN** an `EmailTemplate` whose subject is `"Solicitud para {company_name}"`
- **WHEN** `render(company_name="Acme Corp", unsubscribe_url="http://u")` is called
- **THEN** the returned subject is `"Solicitud para ACME CORP"`

#### Scenario: Mixed-case company name is uppercased in HTML body
- **GIVEN** an `EmailTemplate` whose body contains `"<p>Estimados {company_name},</p>"`
- **WHEN** `render(company_name="Acme Corp", unsubscribe_url="http://u")` is called
- **THEN** the returned body is `"<p>Estimados ACME CORP,</p>"`

#### Scenario: Already-uppercase company name is unaffected
- **GIVEN** a company name already stored as `"TECHCO S.L."`
- **WHEN** `render()` is called
- **THEN** the rendered value is `"TECHCO S.L."` — idempotent, no double-transformation

#### Scenario: Lowercase company name is fully uppercased
- **GIVEN** a company name stored as `"startup labs"`
- **WHEN** `render()` is called
- **THEN** the rendered value is `"STARTUP LABS"`

### Requirement: SystemSettings exposes a configurable displayed-sends floor
`SystemSettings` (`apps/mailing/models.py`) SHALL expose an integer field
`displayed_sends_floor` (default `0`, minimum `0`) that allows administrators
to set a minimum value for the sends count shown publicly on the pricing page.

The field MUST be:
- Registered and editable in the Django admin at `/admin/mailing/systemsettings/`
- `verbose_name` = `"Mínimo de envíos mostrados"` in Spanish
- `help_text` = `"Si el número real de envíos exitosos es menor que este valor, se mostrará este valor en la página de paquetes. Usar 0 para mostrar siempre el valor real."`
- Non-negative (value ≥ 0)
- A Django migration MUST be created to add the column with the default.

The `packages` view in `apps/payments/views.py` MUST read this value via
`SystemSettings.get().displayed_sends_floor` and use it to compute
the final `successful_sends_count` context variable as
`max(real_count, displayed_sends_floor)`.

#### Scenario: Admin can set the floor value
- **GIVEN** a Django staff user with permission to change `SystemSettings`
- **WHEN** they open `/admin/mailing/systemsettings/` and set
  `Mínimo de envíos mostrados` to `500` and save
- **THEN** `SystemSettings.get().displayed_sends_floor` returns `500`
- **AND** the next request to `GET /payments/paquetes/` reflects this value

#### Scenario: Default floor is zero (no artificial inflation)
- **GIVEN** a freshly seeded database with no manual admin configuration
- **WHEN** `SystemSettings.get().displayed_sends_floor` is read
- **THEN** the returned value is `0`
- **AND** the pricing page trust signal is hidden when real sent count is also `0`

#### Scenario: Migration adds column without data loss
- **WHEN** the migration is applied on an existing database
- **THEN** all existing `SystemSettings` rows gain `displayed_sends_floor = 0`
- **AND** no existing field values are altered

