# mailing spec deltas — harden-unsubscribe-flow

## ADDED Requirements

### Requirement: Two-Step Unsubscribe Flow

The `/unsubscribe/<uuid:token>/` endpoint MUST distinguish read-only access (browser fetches, scanner pre-fetch, manual link click) from the explicit opt-out action.
- A `GET` to the URL MUST NOT mutate any persistent state. It MUST render an interstitial confirmation page that includes a CSRF-stamped HTML form whose `action` posts back to the same URL.
- A `POST` to the URL MUST resolve the recipient email from `MailingLog.company_email_snapshot` (falling back to `MailingLog.company.email` if the snapshot is empty), MUST insert or refresh a `Blacklist` row keyed by the lowercased / stripped email via the `Blacklist.add(...)` helper, and MUST set `MailingLog.unsubscribed_at = timezone.now()` on the log row identified by the unsubscribe token **only on the first successful POST**. Subsequent replays against the same token MUST NOT overwrite the original `unsubscribed_at` value — the field captures the moment the recipient first opted out, not the moment of the latest replay.
- The `POST` handler MUST be exempt from Django's CSRF middleware. The unsubscribe token in the URL is the authentication factor.
- Both methods MUST share the existing per-IP rate limit (`10/h`).

#### Scenario: Email-client GET pre-fetch does not blacklist

- **GIVEN** an email recipient whose mail client (Outlook Safe Links, Gmail link scanner, corporate AV proxy) silently fetches every URL inside an incoming message
- **WHEN** the client issues `GET /unsubscribe/<valid-token>/`
- **THEN** the response is `200 OK` rendering the interstitial confirmation page
- **AND** no `Blacklist` row is created
- **AND** the corresponding `MailingLog.unsubscribed_at` remains `NULL`

#### Scenario: Human POST inserts the blacklist row

- **GIVEN** a `MailingLog` whose `company_email_snapshot` is `"contact@empresa.es"` and whose `unsubscribed_at` is `NULL`
- **WHEN** the recipient submits the confirm form (`POST /unsubscribe/<token>/`)
- **THEN** a `Blacklist` row exists with `email == "contact@empresa.es"` and `reason == "unsubscribe"`
- **AND** the same `MailingLog`'s `unsubscribed_at` is set to the current time
- **AND** the response is `200 OK` rendering the success page (`unsubscribe.html`)

#### Scenario: One-click POST without CSRF token still succeeds

- **GIVEN** an MUA implementing RFC 8058 one-click unsubscribe
- **WHEN** the MUA issues `POST /unsubscribe/<token>/` with body `List-Unsubscribe=One-Click` and no CSRF cookie / form token
- **THEN** the request is NOT rejected by CSRF middleware
- **AND** the `Blacklist` row is created exactly as for a human submission

#### Scenario: Idempotent POST preserves the first opt-out timestamp

- **GIVEN** a recipient whose email is already in `Blacklist` because of an earlier successful POST against the same `MailingLog.unsubscribe_token`
- **WHEN** they POST to the same unsubscribe URL again (e.g. mailbox-provider one-click retry, double-click, scanner-issued duplicate)
- **THEN** the response is `200 OK` rendering the success page
- **AND** the existing `Blacklist` row is preserved (no duplicate insert, no `IntegrityError`)
- **AND** `MailingLog.unsubscribed_at` retains the timestamp recorded on the first successful POST and is NOT advanced to the replay's clock time
- **AND** no second `outcome="unsubscribed"` log record is required (the structured-log requirement permits but does not mandate a record on idempotent replays)

#### Scenario: Invalid or unknown token returns 404

- **WHEN** any HTTP method is invoked at `/unsubscribe/<token>/` with a token that does not match any `MailingLog`
- **THEN** the response status is `404 Not Found`
- **AND** no `Blacklist` row is created

#### Scenario: Per-IP rate limit blocks scraping

- **GIVEN** a single client IP issues more than 10 requests against the unsubscribe URL within one hour
- **WHEN** the eleventh request arrives (regardless of method)
- **THEN** the response status is `429 Too Many Requests`
- **AND** no `Blacklist` row is created by the rate-limited request

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
