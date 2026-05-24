## ADDED Requirements

### Requirement: CVFileMissingError exception class

`apps/mailing/engine.py` SHALL define a `CVFileMissingError` exception class (alongside the existing `TokenExpiredError`, `QuotaExceededError`, and `TokenRefreshTransientError`). The `send_cv_email` function SHALL raise `CVFileMissingError` when the user's active CV file cannot be read from storage, instead of setting `is_campaign_active = False` directly and raising a generic `Exception`. The task `process_mailing_queue` SHALL catch `CVFileMissingError` in a dedicated handler that sets both `is_campaign_active = False` and `campaign_pause_reason = "missing_cv"`, saves, and enqueues `send_campaign_paused_notification.delay(user.pk, "missing_cv")` — following the exact pattern of the `TokenExpiredError` and `QuotaExceededError` handlers.

#### Scenario: Missing CV file raises CVFileMissingError

- **GIVEN** a user's active CV record points to a file that does not exist in storage
- **WHEN** `send_cv_email` attempts to read the file
- **THEN** `CVFileMissingError` is raised
- **AND** `is_campaign_active` is NOT modified inside `send_cv_email`

#### Scenario: Task handles CVFileMissingError by pausing and notifying

- **GIVEN** `process_mailing_queue` has called `send_cv_email` for a user whose active CV file is missing
- **WHEN** `CVFileMissingError` is raised
- **THEN** the MailingLog is marked `FAILED`
- **AND** `user.is_campaign_active` is set to `False`
- **AND** `user.campaign_pause_reason` is set to `"missing_cv"`
- **AND** `send_campaign_paused_notification.delay(user.pk, "missing_cv")` is enqueued

## MODIFIED Requirements

### Requirement: Campaign Pause Reason Persistence

The system MUST persist the specific reason why a campaign was automatically paused to provide accurate feedback to the user. The recognised values are `"quota"`, `"expired"`, `"unlinked"`, and `"missing_cv"`.

#### Scenario: Pause reason is saved on error

- **GIVEN** an active campaign
- **WHEN** the system pauses the campaign due to a terminal error
- **THEN** the `User.campaign_pause_reason` MUST be set to the corresponding reason (`quota`, `expired`, `unlinked`, or `missing_cv`).

#### Scenario: Pause reason is cleared on manual action

- **GIVEN** a user with a `campaign_pause_reason` set
- **WHEN** the user manually clicks "Iniciar campaña" or "Pausar campaña"
- **THEN** the `campaign_pause_reason` MUST be cleared (set to empty string).

### Requirement: Dashboard Warning Banner

The dashboard UI MUST display a clear explanation and call to action if the campaign was paused by the system, for any of the recognised pause reasons.

#### Scenario: User sees Quota warning

- **GIVEN** a user with `campaign_pause_reason = "quota"`
- **WHEN** the user views their dashboard
- **THEN** a warning banner MUST be visible stating that the daily provider limit was reached.

#### Scenario: User sees Expired warning

- **GIVEN** a user with `campaign_pause_reason = "expired"`
- **WHEN** the user views their dashboard
- **THEN** a warning banner MUST be visible stating that the email session has expired, with a link to re-link their account.

#### Scenario: User sees Unlinked warning

- **GIVEN** a user with `campaign_pause_reason = "unlinked"`
- **WHEN** the user views their dashboard
- **THEN** a warning banner MUST be visible stating that their email account was disconnected, with a link to re-link their account.

#### Scenario: User sees Missing CV warning

- **GIVEN** a user with `campaign_pause_reason = "missing_cv"`
- **WHEN** the user views their dashboard
- **THEN** a warning banner MUST be visible stating that the CV file is missing and the campaign has been paused, advising the user to re-upload their CV from the dashboard.

### Requirement: Reasoned Campaign Pause Notifications

When a campaign is paused by the system due to a terminal error, the notification sent to the user MUST clearly state the reason for the pause. A notification MUST also be sent when the CV file is unavailable or when the user's OAuth account is disconnected.

#### Scenario: Email for Quota Reached

- **GIVEN** a campaign is paused because of a `QuotaExceededError`
- **THEN** the email sent MUST specify that the **provider-enforced** limit was reached and the user should wait until tomorrow.

#### Scenario: Email for Token Expired

- **GIVEN** a campaign is paused because of a `TokenExpiredError`
- **THEN** the email sent MUST specify that the email session has expired and provide a link to re-link the account.

#### Scenario: Email for OAuth Unlinked

- **GIVEN** a campaign is paused because the user disconnected their OAuth account
- **THEN** the `pause_campaign_on_unlink` signal handler MUST enqueue `send_campaign_paused_notification.delay(user.pk, "unlinked")`
- **AND** the email sent MUST specify that the email account was disconnected and provide a link to re-link the account.

#### Scenario: Email for Missing CV

- **GIVEN** a campaign is paused because the active CV file could not be read from storage
- **THEN** the email sent MUST specify that the CV file is no longer available and the user should upload a new CV from the dashboard.

### Requirement: CV PDF Attachments

The mailing engine MUST attach the user's active CV as a PDF file directly to the outgoing email message for both Google and Microsoft providers. The attachment MUST be correctly encoded (base64) and specify the `application/pdf` content type. The system MUST gracefully handle file read errors if the physical file is missing from storage by pausing the campaign with reason `"missing_cv"` and enqueuing a notification to the user.

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

#### Scenario: Missing physical CV file pauses campaign and notifies user

- **GIVEN** a user's active CV record points to a file that does not exist in storage
- **WHEN** `send_cv_email` is called
- **THEN** a `CVFileMissingError` is raised
- **AND** the calling task pauses the campaign (`is_campaign_active = False`, `campaign_pause_reason = "missing_cv"`)
- **AND** `send_campaign_paused_notification` is enqueued with `reason="missing_cv"`
- **AND** the MailingLog for this attempt is marked `FAILED`