# Spec Delta: Improved Pause Notifications and UI Feedback

## ADDED Requirements

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
