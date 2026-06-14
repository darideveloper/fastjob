## Context

FastJob sends emails containing CVs to employers on behalf of job-seekers. Currently, active campaigns send emails continuously throughout the day and night as long as they have credits remaining. Sending emails outside normal business hours looks unprofessional and leads to lower conversion and higher spam reports.

This design introduces a globally configurable active sending window, pauses active campaigns when entering off-hours, and automatically resumes them when the sending window reopens, while respecting the hidden credit multiplier rules.

## Goals / Non-Goals

**Goals:**
- Restrict email delivery to a globally defined active sending window (e.g. 10:00 AM to 8:00 PM).
- Auto-pause all active campaigns when off-hours start, updating the database status to allow the dashboard to display the paused reason.
- Auto-resume campaigns in the morning only if they still have credits remaining, ensuring compatibility with the hidden multiplier limit logic.
- Inform users when their campaign is paused via a clear dashboard banner and a pause email notification.

**Non-Goals:**
- Allowing user-specific time windows (this is a global setting).
- Pausing campaigns that were manually stopped by the user.

## Decisions

### 1. Database-Backed Settings
- **Decision**: Add `email_sending_start_time` and `email_sending_end_time` to the `SystemSettings` singleton model.
- **Rationale**: This allows admins to adjust active sending hours dynamically via the Django Admin panel without deploying code changes.
- **Alternatives Considered**: Using django settings (`settings.py`). Rejected because changing hours would require redeploying the application.

### 2. Time Window Enforcement in Periodic Celery Task
- **Decision**: Check time-window compliance directly inside the existing `process_mailing_queue` Celery task.
- **Rationale**: Since `process_mailing_queue` runs every minute, it can easily detect timezone transitions, perform bulk status updates, and avoid processing sends when off-hours.
- **Implementation**:
  - We evaluate local time in the system timezone (defined as `Europe/Madrid` in Django settings) using `timezone.localtime(timezone.now()).time()`.
  - To support windows spanning midnight, we check if `start <= end` and use `start <= current <= end`, else `current >= start or current <= end`.
  - When off-hours start, we bulk-pause active campaigns by updating `is_campaign_active=False` and `campaign_pause_reason='time_window'`.
  - When on-hours start, we bulk-resume campaigns with `campaign_pause_reason='time_window'` whose balance satisfies the hidden multiplier check: `credits_remaining > -extra_limit`.
- **Alternatives Considered**: Having separate Celery beat cron tasks at exactly 10:00 AM and 8:00 PM. Rejected because if Celery or the server is down during the transition minute, the events are missed entirely. Checking in the main loop is self-healing.

### 3. Credit Multiplier Math Integration
- **Decision**: Resume check calculates the user's real credit limit including the hidden multiplier:
  ```python
  extra_limit = math.ceil(user.total_purchased_credits * (float(cfg.hidden_credit_multiplier) - 1.0))
  has_credits = user.credits_remaining > -extra_limit
  ```
- **Rationale**: If a user runs out of virtual credits (`credits_remaining = 0`), they still have multiplier credits. The campaign must resume the next day to send the multiplier emails (up to the real limit). If they hit the real limit (`credits_remaining <= -extra_limit`), the campaign transitions to a permanent `quota` pause.

### 4. Admin UI Registration
- **Decision**: Explicitly register `email_sending_start_time` and `email_sending_end_time` within `SystemSettingsAdmin` fieldsets in `apps/mailing/admin.py`.
- **Rationale**: Because the settings admin view utilizes custom, explicit `fieldsets`, new database columns on the `SystemSettings` singleton model are hidden by default. Registering them under a new dedicated fieldset makes them editable in the Django admin dashboard.

### 5. Manual Activation Off-Hours Handling
- **Decision**: Inside `toggle_campaign` in `apps/dashboard/views.py`, evaluate the active sending window during the manual campaign activation request. If it is off-hours, activate the campaign directly in the scheduled/paused state (`is_campaign_active = False` and `campaign_pause_reason = "time_window"`) with a custom scheduled message.
- **Rationale**: This prevents a bad user experience where activating a campaign during the night successfully runs, but is immediately bulk-paused by the next Celery tick, triggering a redundant "campaign paused" email notification.

## Risks / Trade-offs

- **Risk**: Daily emails could spam the user's inbox every night when their campaign is paused.
- **Mitigation**: Add a checkbox `notify_on_time_window_pause` to `SystemSettings` (default `False` or only notify once per campaign lifetime). Alternatively, the proposal assumes we send it, but we can configure it to be silent or limit frequency. Also, by checking the time window in `toggle_campaign` directly, we prevent sending notification emails when users manually schedule campaigns at night.

### 6. Validation and Migration Safety
- **Decision**: Define the fields `email_sending_start_time` and `email_sending_end_time` with non-null constraints and explicit defaults (`10:00` and `20:00` respectively).
- **Rationale**: Singleton model instances in production databases require concrete values during migrations, and non-null values prevent `TypeError` checks in the worker task.
- **Decision**: Implement model-level validation in `SystemSettings.clean` to raise a validation error if start and end times are identical.

### 7. User Control & Dashboard Feedback for Paused State
- **Decision**: In the dashboard view, if `campaign_pause_reason == "time_window"`, render the "Pausar campaña" button. If the user clicks "Pausar", set `is_campaign_active = False` and clear `campaign_pause_reason`.
- **Decision**: Show the configured active sending window in the dashboard header/toggle section even when the campaign is active.
- **Rationale**: This gives the user full control to cancel their campaign from resuming during off-hours, and provides clear visibility of the campaign's active running window.

