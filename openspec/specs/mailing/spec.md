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

