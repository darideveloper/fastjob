## MODIFIED Requirements
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
