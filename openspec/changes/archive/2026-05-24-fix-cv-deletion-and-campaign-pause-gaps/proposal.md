# Change: Fix CV-deletion and campaign-pause gaps

## Why

Four related bugs leave users without explanation when their campaign stops, plus a pre-existing notification gap:

1. **Deleting any CV while the campaign is active** is allowed, causing either a silent CV switch (fallback to next-most-recent) or a silent campaign pause (if it was the only CV) with no `campaign_pause_reason`, no dashboard banner, and no notification email.

2. **Direct POST to the delete endpoint** bypasses any template-level hiding — there is no server-side guard preventing CV deletion during an active campaign.

3. **The `send_cv_email` engine** pauses the campaign when the S3 file is unreadable but does not set `campaign_pause_reason` or send a notification — same silent-pause gap. It also sets `is_campaign_active = False` inside the engine, inconsistent with the pattern used for `TokenExpiredError` and `QuotaExceededError` (where the task owns pausing).

4. **The `send_campaign_paused_notification` task** silently returns for `reason="unlinked"`, sending no email — a pre-existing notification gap affecting users who disconnect their OAuth account. Additionally, the `pause_campaign_on_unlink` signal handler never enqueues the notification task at all, so even adding an `unlinked` branch to the function would have no effect without also calling it.

## What Changes

- **Server-side guard**: `delete_cv` view rejects deletion of any CV when `user.is_campaign_active` is `True`, returning a clear Spanish error message. This blocks both UI and direct-POST paths.
- **Template-level hide**: The "Eliminar" button is hidden for all CVs when the campaign is active (belt-and-braces; the server is authoritative).
- **Typed exception for CV read failures**: Replace the generic `Exception(f"Failed to read CV file: ...")` in `send_cv_email` with a `CVFileMissingError` exception class, matching the pattern of `TokenExpiredError` and `QuotaExceededError`.
- **Task-level pause and notification**: Move campaign pausing for CV-read failures from the engine to the task (alongside the existing `TokenExpiredError`/`QuotaExceededError` handlers), setting `campaign_pause_reason = "missing_cv"` and enqueuing `send_campaign_paused_notification`.
- **New pause reason**: A `"missing_cv"` value is added to the set of recognised `campaign_pause_reason` values, with a corresponding dashboard warning banner and notification email.
- **Fill unlinked notification gap**: Add an `unlinked` branch to `send_campaign_paused_notification` so users who disconnect their OAuth account also receive an explanatory email, and enqueue the notification from the `pause_campaign_on_unlink` signal handler.

## Impact

- Affected specs: **dashboard** (CV deletion guard, pause-reason banner), **mailing** (engine CV-read-failure handling, notification email, pause-reason values), **accounts** (document `missing_cv` as a valid pause reason, unlinked notification signal)
- Affected code: `apps/dashboard/views.py`, `apps/mailing/engine.py`, `apps/mailing/tasks.py`, `apps/accounts/signals.py`, `templates/dashboard/index.html`