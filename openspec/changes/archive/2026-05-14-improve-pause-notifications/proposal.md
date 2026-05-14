# Proposal: Improve Campaign Pause Notifications and UI Feedback (UX)

## Why
Currently, when a campaign is paused due to a terminal error, the user receives a generic "re-link your account" email. This is misleading when the failure is due to a **Daily Message Limit (Quota) enforced by the email provider (Gmail/Outlook)**. Furthermore, the dashboard UI does not explain *why* the campaign was paused, leaving users confused when they see their campaign has stopped without their intervention.

## What Changes
### 1. Model & Error Detection (`apps/accounts/models.py`, `apps/mailing/engine.py`)
- Add a `campaign_pause_reason` field to the `User` model (choices: `expired`, `quota`, `unlinked`).
- Define a new `QuotaExceededError` exception in `engine.py`.
- Update `_send_via_microsoft` and `_send_via_gmail` to detect provider-enforced daily limits and raise `QuotaExceededError`.

### 2. Task & Signal Handling (`apps/mailing/tasks.py`, `apps/accounts/signals.py`)
- Update `process_mailing_queue` to catch `QuotaExceededError` and `TokenExpiredError`, setting the appropriate `campaign_pause_reason` on the user.
- Update the `social_account_removed` signal to set `campaign_pause_reason='unlinked'`.
- Refactor notification logic to send dynamic emails based on the reason.

### 3. Dashboard UI (`apps/dashboard/views.py`, `templates/dashboard/index.html`)
- Update `toggle_campaign` view to clear `campaign_pause_reason` when the user manually starts or stops the campaign.
- Add a prominent warning banner to the dashboard that displays a specific message based on the `campaign_pause_reason`.

## Impact
- **Transparent UX**: Users know exactly why their campaign stopped, whether it's a session expiry, a provider limit, or an unlinked account.
- **Actionable Guidance**: The UI tells the user if they need to re-link or simply wait until tomorrow.
- **Consistency**: Unified feedback across email and dashboard.
