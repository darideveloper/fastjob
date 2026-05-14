# Change: Add Global Email Visibility Toggle

## Why
Currently, emails sent via Microsoft Graph do not save to the user's "Sent" folder, while emails sent via Gmail API do. The client wants to be able to enable or disable the visibility of sent emails globally for all users from a system configuration dashboard (Django Admin).

## What Changes
- **Database/Admin**: Create a global singleton `SystemConfig` model in `apps/core/models.py` to hold a boolean field `save_emails_to_sent_folder`. This will be editable from the Django Admin dashboard.
- **Microsoft Graph**: Update `_send_via_microsoft` in `apps/mailing/engine.py` to pass the globally configured value of `save_emails_to_sent_folder` to the `saveToSentItems` API parameter.
- **Gmail API**: Update `_send_via_gmail` in `apps/mailing/engine.py` to immediately delete the message if the global `save_emails_to_sent_folder` is `False`.
- **Google OAuth Scope**: Update the required Google OAuth scopes in `config/settings.py` from `gmail.send` to `gmail.modify` so the system can delete the sent messages.
- **BREAKING**: Changing the Gmail OAuth scope will require existing users to re-authenticate and consent to the new permissions. It also requires the Google Cloud Project to undergo a CASA Tier 2/3 security audit for the restricted `gmail.modify` scope.

## Impact
- Affected specs: `mailing`
- Affected code: `apps/core/models.py`, `apps/core/admin.py`, `apps/mailing/engine.py`, `config/settings.py`
