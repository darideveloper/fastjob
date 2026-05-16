## MODIFIED Requirements

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
