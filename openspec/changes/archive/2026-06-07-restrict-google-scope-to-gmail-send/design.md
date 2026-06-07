## Context

The project uses `gmail.modify` OAuth scope to support a "don't save to sent folder" feature controlled by `SystemSettings.save_emails_to_sent_folder`. When disabled, the Gmail send path trashes the sent message after delivery, and the Microsoft Graph path sends with `saveToSentItems: false`. This feature is not essential to the core product — users send CVs and expect them to appear in their sent folder. The broader scope (`gmail.modify` grants read/write/delete on the entire mailbox) is disproportionate to the actual need (send only).

## Goals / Non-Goals

**Goals:**
- Remove `save_emails_to_sent_folder` field from `SystemSettings` model and all associated UI/logic
- Remove Gmail trash calls from `_send_via_gmail` in `engine.py`
- Remove Microsoft `saveToSentItems` conditional — always send with `true`
- Change Google OAuth scope from `gmail.modify` to `gmail.send`
- Remove or rewrite tests that cover visibility-off behavior
- Update the mailing spec to remove the Visibility Toggle requirement and visibility-off scenarios
- Handle migration: remove the `save_emails_to_sent_folder` column from `mailing_systemsettings`

**Non-Goals:**
- No changes to the Microsoft OAuth scope (`Mail.Send` is already the minimum)
- No changes to the core sending flow aside from removing the conditional trash
- No UI/UX changes to the dashboard or templates (the toggle is admin-only)
- No changes to the Google Cloud Console configuration (documented as a manual step)

## Decisions

### 1. New migration to remove the column
**Decision**: Remove the field from the model and run `manage.py makemigrations` to generate a new migration. Existing migration files are untouched — they stay in the history. The new migration simply applies `RemoveField` on `SystemSettings.save_emails_to_sent_folder`.

### 2. Microsoft path: always `saveToSentItems: true`
**Decision**: Remove the conditional in `_send_via_microsoft` and always pass `"saveToSentItems": True` in the JSON payload. This is the natural behavior users expect — sent emails appear in their Outlook Sent Items folder.

### 3. Gmail path: remove trash logic entirely
**Decision**: Remove the `if not save_emails_to_sent_folder` block in `_send_via_gmail` (lines 297–309 in current `engine.py`). The send call is unchanged — it already posts to the correct endpoint.

### 4. Test strategy
**Decision**: Remove the tests that specifically verify the trash behavior (`test_send_cv_email_via_google_honors_visibility_disabled_by_trashing`, `test_send_cv_email_via_google_honors_visibility_enabled_by_not_trashing`). Update any tests that reference `save_emails_to_sent_folder` in their setup (e.g., `test_send_cv_email_via_google_honors_visibility_disabled_by_trashing`). The core send tests remain unchanged.

## Risks / Trade-offs

- **[Low] Users who preferred the "don't save to sent" behavior lose it**: No users have requested this feature; it was admin-configurable only. Mitigation: documented in release notes.
- **[Low] Migration removes column with data**: If admin had set `save_emails_to_sent_folder = True`, the column and its value are dropped. Mitigation: the admin field is removed anyway; the new behavior always saves to sent folder, which is the default expected behavior.
- **[Low] Google Cloud Console change is manual**: The scope reduction requires updating the OAuth consent screen in Google Cloud Console. This is a one-time manual step that must be documented in the deployment checklist. Existing tokens are unaffected (they were issued with `gmail.modify` and have broader permissions than needed — this is safe, not risky).
