## 1. Database Setup

- [x] 1.1 Add `email_sending_start_time` and `email_sending_end_time` TimeFields (with default values `10:00` and `20:00` respectively) to `SystemSettings` in `apps/mailing/models.py`. Implement validation in `clean()` to prevent identical start/end times.
- [x] 1.2 Create and run the Django database migrations.
- [x] 1.3 Update `SystemSettingsAdmin` in `apps/mailing/admin.py` to display the new fields under a dedicated "Horario de Envío (Global)" fieldset.

## 2. Queue Enforcement & Auto-Resume

- [x] 2.1 In `apps/mailing/tasks.py::process_mailing_queue`, extract configured start and end times and evaluate timezone-aware sending window compliance.
- [x] 2.2 In `process_mailing_queue`, if outside active hours, bulk-pause active campaigns setting `is_campaign_active = False` and `campaign_pause_reason = "time_window"` and enqueue notification emails.
- [x] 2.3 In `process_mailing_queue`, if inside active hours, bulk-resume campaigns paused with `time_window` whose credits satisfy the hidden multiplier limit (`credits_remaining > -extra_limit`).
- [x] 2.4 In `process_mailing_queue`, if a paused campaign has no credits left (reaches the multiplier limit), transition its reason to `quota` and enqueue a quota notification.

## 3. Email Templates & UI Banner

- [x] 3.1 Update `campaign_paused_notification.html` and `campaign_paused_notification.txt` templates with custom copy for the `time_window` pause reason.
- [x] 3.2 In `apps/dashboard/views.py::index`, query `SystemSettings` and inject it as `system_settings` into the template context.
- [x] 3.3 In `templates/dashboard/index.html`, update the alert banner to handle `time_window` reason and display the active sending hours dynamically. Also show a text indicator of active sending hours in the header when the campaign is running.
- [x] 3.4 In `apps/dashboard/views.py::toggle_campaign`, when starting a campaign, evaluate the active sending window. If off-hours, directly set `is_campaign_active = False` and `campaign_pause_reason = "time_window"`, and output a custom scheduled success message. If stopping the campaign (`action == "stop"`), reset the `campaign_pause_reason` field to prevent auto-resume.
- [x] 3.5 In `templates/dashboard/index.html`, update the campaign toggle button checks so that it renders the "Pausar campaña" button if `user.is_campaign_active` is `True` OR `user.campaign_pause_reason` is `"time_window"`.

## 4. Tests & Verification

- [x] 4.1 Write unit tests in `apps/mailing/tests/test_tasks.py` to verify that `process_mailing_queue` skips email sending outside configured hours.
- [x] 4.2 Write tests to verify bulk-pausing on off-hours transition and bulk-resuming on on-hours transition.
- [x] 4.3 Write tests to verify that time-window resume correctly respects the hidden multiplier limit (resuming at `0` credits, stopping at the real limit).
- [x] 4.4 Write tests to verify that `toggle_campaign` view correctly schedules the campaign in "time_window" pause status when manual start is requested during off-hours, and that no email is sent.
- [x] 4.5 Write tests to verify that clicking "Pausar" during a time window pause successfully stops the campaign and clears the pause reason, preventing auto-resume.

