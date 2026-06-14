## Why

To maintain business professionalism and reduce spam complaints, FastJob needs to restrict CV email delivery to specific business hours (e.g., 10:00 AM to 8:00 PM). Delivering emails during off-hours looks unprofessional to companies and increases the likelihood of job-seeker applications being ignored or marked as spam.

## What Changes

- Add global start and end time settings for email sending to `SystemSettings` (e.g., default 10:00 AM to 8:00 PM).
- Update the periodic mailing queue runner to pause email sending outside the active time window, auto-pausing active campaigns with a specific `time_window` reason.
- Auto-resume campaigns once the active time window starts again, provided the user still has credits remaining (taking into account the hidden multiplier: if virtual credits hit 0, the campaign is resumed because they still have multiplier credits left).
- Show clear feedback in the client dashboard when a campaign is temporarily paused for the night window, and display the active sending hours window when the campaign is running.
- Send a one-time notification email when the campaign transitions to a time-window pause.
- Update manual campaign starting in the dashboard to immediately transition to `time_window` pause (without notification spam) if started during off-hours, and allow users to pause/cancel the campaign from this scheduled state to prevent auto-resume.


## Capabilities

### New Capabilities
- None

### Modified Capabilities
- mailing: Restrict the daily sending queue to a global time window, auto-pause active campaigns when the window ends, and auto-resume them when the window starts (evaluating credit availability including the hidden multiplier bonus).
- dashboard: Visualize the campaign off-hours pause state with a descriptive banner including the configured start/end times.

## Impact

- **Models**: `SystemSettings` in `apps/mailing/models.py` will have two new fields: `email_sending_start_time` and `email_sending_end_time`.
- **Admin**: `SystemSettingsAdmin` in `apps/mailing/admin.py` will display the new fields in a separate fieldset.
- **Tasks**: `process_mailing_queue` in `apps/mailing/tasks.py` will handle active hour checks, pausing campaigns, and auto-resuming them.
- **Views & Templates**: Dashboard index in `apps/dashboard/views.py` will inject system settings to show active times in `templates/dashboard/index.html`. `toggle_campaign` in `apps/dashboard/views.py` will detect off-hours manual start and schedule the campaign as paused (`time_window`). Email templates for campaign pauses will be updated to handle the `time_window` reason.
