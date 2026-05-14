# Spec Delta: Mailing Engine Hardening

## ADDED Requirements

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
