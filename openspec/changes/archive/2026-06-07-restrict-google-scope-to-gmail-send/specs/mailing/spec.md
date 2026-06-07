## REMOVED Requirements

### Requirement: Global Email Visibility Toggle

**Reason**: The Google OAuth scope was reduced from `gmail.modify` (full mailbox access) to `gmail.send` (send-only). The trashing operation that required `gmail.modify` is removed. The Microsoft `saveToSentItems` conditional is removed — sent emails always appear in the user's Sent Items folder.

**Migration**:
- `SystemSettings.save_emails_to_sent_folder` field is removed from the model and admin.
- The corresponding migration (`mailing 0011`) stays in place; a new migration removes the column.
- `_send_via_gmail` no longer trashes messages — it only calls `users.messages.send`.
- `_send_via_microsoft` always passes `"saveToSentItems": true`.

### Requirement: Sending via Gmail API with visibility off

**Reason**: Removed together with the Global Email Visibility Toggle. The Gmail path always uses `users.messages.send` without post-send trashing.

### Requirement: Sending via Microsoft Graph with visibility off

**Reason**: Removed together with the Global Email Visibility Toggle. The Microsoft path always sends with `saveToSentItems: true`.

## MODIFIED Requirements

### Requirement: Email API Integration

The system MUST dispatch CV emails via the authenticated user's chosen provider using their native APIs (Gmail API for Google, Microsoft Graph API for Microsoft). The system MUST handle authentication state securely and appropriately for background task dispatch.

#### Scenario: Sending via Gmail API

- **WHEN** a CV email is dispatched via a linked Google account
- **THEN** the system calls the `users.messages.send` endpoint
- **AND** no post-send operations (trash, delete) are performed

#### Scenario: Sending via Microsoft Graph

- **WHEN** a CV email is dispatched via a linked Microsoft account
- **THEN** the system calls the `sendMail` endpoint with `"saveToSentItems": true`
- **AND** the sent email appears in the user's Outlook Sent Items folder
