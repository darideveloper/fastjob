## ADDED Requirements

### Requirement: Global Time-Window Email Sending Limit
The mailing engine SHALL only process the mailing queue and send emails during the active hours defined by `SystemSettings.email_sending_start_time` and `SystemSettings.email_sending_end_time`. If the current time (in the configured server timezone) is outside this window, all campaigns currently marked as active (`is_campaign_active = True`) MUST be paused, setting `is_campaign_active = False` and `campaign_pause_reason = "time_window"`.

#### Scenario: Queue runs outside the active hours window
- **GIVEN** a user with an active campaign
- **AND** the current local time is outside the configured sending hours window
- **WHEN** the mailing queue runs
- **THEN** no email is sent
- **AND** the campaign is paused with reason "time_window"
- **AND** a campaign paused notification is sent for "time_window"

#### Scenario: Queue runs inside the active hours window and resumes time-window paused campaigns
- **GIVEN** a user with a campaign paused with reason "time_window"
- **AND** the user has remaining credits including the multiplier bonus (`credits_remaining > -extra_limit`)
- **AND** the current local time is inside the configured sending hours window
- **WHEN** the mailing queue runs
- **THEN** the campaign is resumed (`is_campaign_active` is set to `True` and `campaign_pause_reason` is cleared)
- **AND** email sending proceeds normally

#### Scenario: Campaign does not resume if no credits remain
- **GIVEN** a user with a campaign paused with reason "time_window"
- **AND** the user has no credits remaining including the multiplier bonus (`credits_remaining <= -extra_limit`)
- **AND** the current local time is inside the configured sending hours window
- **WHEN** the mailing queue runs
- **THEN** the campaign remains paused and its reason is updated to "quota"
- **AND** a campaign paused notification is sent for "quota"
### Requirement: SystemSettings Configuration Validation
The `SystemSettings` model clean method and the Django admin panel SHALL enforce that the `email_sending_start_time` and `email_sending_end_time` are not identical to prevent accidental 24-hour campaign locking.

#### Scenario: Identical start and end times validation
- **GIVEN** the admin is configuring SystemSettings
- **WHEN** they set identical start and end times and attempt to save
- **THEN** a ValidationError is raised preventing the save.

## MODIFIED Requirements

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

#### Scenario: User sees Time Window warning

- **GIVEN** a user with `campaign_pause_reason = "time_window"`
- **WHEN** the user views their dashboard
- **THEN** a warning banner MUST be visible stating that the campaign is paused for off-hours and will automatically resume.

### Requirement: Reasoned Campaign Pause Notifications

When a campaign is paused by the system due to a terminal error, the notification sent to the user MUST use the branded email layout (`templates/email/base.html`) and MUST be sent as an `EmailMultiAlternatives` message with both plain-text and HTML alternatives. The HTML alternative MUST include the FastJob logo, a colored header, and the standard footer. The plain-text body MUST contain the same informational content as the HTML alternative without markup.

A notification MUST also be sent when the CV file is unavailable or when the user's OAuth account is disconnected.

#### Scenario: Email for Quota Reached

- **GIVEN** a campaign is paused because of a `QuotaExceededError`
- **THEN** the email sent MUST specify that the **provider-enforced** limit was reached and the user should wait until tomorrow.
- **AND** the HTML alternative MUST use the branded email layout with logo, header, and footer.

#### Scenario: Email for Token Expired

- **GIVEN** a campaign is paused because of a `TokenExpiredError`
- **THEN** the email sent MUST specify that the email session has expired and provide a link to re-link the account.
- **AND** the HTML alternative MUST use the branded email layout with logo, header, and footer.

#### Scenario: Email for OAuth Unlinked

- **GIVEN** a campaign is paused because the user disconnected their OAuth account
- **THEN** the `pause_campaign_on_unlink` signal handler MUST enqueue `send_campaign_paused_notification.delay(user.pk, "unlinked")`
- **AND** the email sent MUST specify that the email account was disconnected and provide a link to re-link the account.
- **AND** the HTML alternative MUST use the branded email layout with logo, header, and footer.

#### Scenario: Email for Missing CV

- **GIVEN** a campaign is paused because the active CV file could not be read from storage
- **THEN** the email sent MUST specify that the CV file is no longer available and the user should upload a new CV from the dashboard.
- **AND** the HTML alternative MUST use the branded email layout with logo, header, and footer.

#### Scenario: Email for Time Window Pause

- **GIVEN** a campaign is paused because the current time is outside active sending hours
- **THEN** the email sent MUST specify that the campaign is temporarily paused for off-hours and will automatically resume tomorrow.
- **AND** the HTML alternative MUST use the branded email layout with logo, header, and footer.

