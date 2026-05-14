## ADDED Requirements

### Requirement: Global Email Visibility Toggle
The system SHALL provide a global configuration toggle in the system dashboard (Django Admin) to determine whether sent CV emails are saved to the user's "Sent Items" folder.

#### Scenario: Admin toggles visibility on
- **WHEN** an admin sets the email visibility toggle to `True`
- **THEN** emails sent via both Microsoft and Google OAuth accounts are saved to all users' respective sent folders.

#### Scenario: Admin toggles visibility off
- **WHEN** an admin sets the email visibility toggle to `False`
- **THEN** emails sent via Microsoft do not appear in the sent folder AND emails sent via Gmail are immediately deleted from the user's mailbox across all users.

## MODIFIED Requirements

### Requirement: Email API Integration
The system MUST dispatch CV emails via the authenticated user's chosen provider using their native APIs (Gmail API for Google, Microsoft Graph API for Microsoft). The system MUST handle authentication state securely and appropriately for background task dispatch.

#### Scenario: Sending via Microsoft Graph with visibility off
- **WHEN** a CV email is dispatched via a linked Microsoft account AND the global visibility toggle is `False`
- **THEN** the system calls the `sendMail` endpoint with `saveToSentItems` set to `False`.

#### Scenario: Sending via Microsoft Graph with visibility on
- **WHEN** a CV email is dispatched via a linked Microsoft account AND the global visibility toggle is `True`
- **THEN** the system calls the `sendMail` endpoint with `saveToSentItems` set to `True`.

#### Scenario: Sending via Gmail API with visibility off
- **WHEN** a CV email is dispatched via a linked Google account AND the global visibility toggle is `False`
- **THEN** the system calls the `users.messages.send` endpoint, retrieves the message ID, and subsequently calls `users.messages.trash` or `users.messages.delete` to remove it from the Sent folder.

#### Scenario: Sending via Gmail API with visibility on
- **WHEN** a CV email is dispatched via a linked Google account AND the global visibility toggle is `True`
- **THEN** the system calls the `users.messages.send` endpoint and does not attempt to delete it.
