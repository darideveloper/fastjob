# mailing Specification

## ADDED Requirements

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
