## Why

The current Google OAuth integration requests `gmail.modify` scope, which grants full read/write/delete access to users' Gmail mailboxes. This is excessive for the project's actual needs — the mailing engine only sends emails. The `gmail.modify` scope was originally required to support the "don't save to sent folder" feature (which trashes sent messages), but this feature adds unnecessary permission risk and complexity for minimal value.

Reducing to `gmail.send` (the narrowest scope for sending) improves user trust, makes the Google OAuth consent screen less intimidating, and reduces security surface area.

## What Changes

**REMOVED — "Don't Save to Sent Folder" feature:**
- Remove `save_emails_to_sent_folder` field from `SystemSettings` model
- Remove the "Visibilidad de Correos" fieldset from `SystemSettingsAdmin`
- Remove the Gmail trash logic from `_send_via_gmail` in `engine.py`
- Remove the Microsoft `saveToSentItems` conditional in `_send_via_microsoft` (always send with `saveToSentItems: true`)
- Create a new Django migration via `makemigrations` to remove the column — existing migration files are not touched
- Update tests that cover the trash behavior

**REDUCED — Google OAuth scope:**
- Change `SOCIALACCOUNT_PROVIDERS['google']['SCOPE']` from `gmail.modify` to `gmail.send`
- This is the minimum scope required to send email via the Gmail API

## Capabilities

### New Capabilities
*(none — this is a removal/reduction change)*

### Modified Capabilities
- `mailing`: Remove the `Global Email Visibility Toggle` requirement and all related scenarios. Remove the visibility-off send scenarios for both Gmail and Microsoft paths. The `Email API Integration` requirement's visibility scenarios are removed; the Gmail path always sends without trashing, and the Microsoft path always sends with `saveToSentItems: true`.
*(none — the accounts spec has no scope-specific requirements)*

## Impact

- **`apps/mailing/models.py`**: Remove `save_emails_to_sent_folder` field
- **`apps/mailing/admin.py`**: Remove "Visibilidad de Correos" fieldset
- **`apps/mailing/engine.py`**: Remove Gmail trash logic; simplify Microsoft `saveToSentItems` to always `true`
- **`config/settings.py`**: Change `gmail.modify` → `gmail.send` in SOCIALACCOUNT_PROVIDERS
- **`apps/mailing/migrations/`**: Generate a new migration with `manage.py makemigrations` — existing migration files are untouched
- **`apps/mailing/tests/`**: Remove or rewrite tests for visibility-off scenarios
- **`openspec/specs/mailing/spec.md`**: Remove the `Global Email Visibility Toggle` requirement and its scenarios; update `Email API Integration` scenarios to remove visibility variants
- **`templates/legal/privacy.html`**: Change `gmail.modify` → `gmail.send` in the privacy policy text
- **`openspec/specs/legal/spec.md`**: Update scope reference from `gmail.modify` → `gmail.send`
- **`README.md`**: Update scope reference and setup instructions from `gmail.modify` → `gmail.send` (two sites: line 12 and line 46)
- **`.env` / `.env.example`**: No changes needed (no env vars involved)
- **Google Cloud Console**: Update OAuth consent screen scope from `gmail.modify` to `gmail.send` (manual step in Google Cloud Console — documented but not automated)
