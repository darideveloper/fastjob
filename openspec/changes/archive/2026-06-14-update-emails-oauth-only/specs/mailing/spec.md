## MODIFIED Requirements

### Requirement: Reasoned Campaign Pause Notifications

When a campaign is paused by the system due to a terminal error, the notification sent to the user MUST use the branded email layout (`templates/email/base.html`) and MUST be sent as an `EmailMultiAlternatives` message with both plain-text and HTML alternatives. The HTML alternative MUST include the FastJob logo, a colored header, and the standard footer. The plain-text body MUST contain the same informational content as the HTML alternative without markup.

A notification MUST also be sent when the CV file is unavailable or when the user's OAuth account session is expired/disconnected. If the email fails to send, the exception MUST be caught and logged at ERROR level with a full stack trace (`exc_info=True`), and the task must exit cleanly without throwing unhandled errors or triggering Celery retries.

#### Scenario: Email for Quota Reached

- **GIVEN** a campaign is paused because of a `QuotaExceededError`
- **THEN** the email sent MUST specify that the **provider-enforced** limit was reached and the user should wait until tomorrow.
- **AND** the HTML alternative MUST use the branded email layout with logo, header, and footer.

#### Scenario: Email for Token Expired

- **GIVEN** a campaign is paused because of a `TokenExpiredError`
- **THEN** the email sent MUST specify that the email session has expired and instruct the user to log in again to FastJob to renew the connection.
- **AND** the HTML alternative MUST use the branded email layout with logo, header, and footer.

#### Scenario: Email for OAuth Unlinked

- **GIVEN** a campaign is paused because the user's OAuth account connection was disconnected or revoked
- **THEN** the `pause_campaign_on_unlink` signal handler MUST enqueue `send_campaign_paused_notification.delay(user.pk, "unlinked")`
- **AND** the email sent MUST specify that the email account was disconnected and instruct the user to log in again to FastJob to renew the connection.
- **AND** the HTML alternative MUST use the branded email layout with logo, header, and footer.

#### Scenario: Email for Missing CV

- **GIVEN** a campaign is paused because of a `CVFileMissingError`
- **THEN** the email sent MUST specify that the CV file is missing and provide advice to re-upload it.
- **AND** the HTML alternative MUST use the branded email layout with logo, header, and footer.

#### Scenario: SMTP failure during campaign pause email is logged

- **GIVEN** the SMTP server is unreachable
- **WHEN** `send_campaign_paused_notification.delay(user.pk, "expired")` executes
- **THEN** the exception is caught and logged at ERROR level with a full stack trace.
