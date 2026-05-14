# Tasks: Improve Campaign Pause Notifications and UI Feedback

- [x] 1. **Model & Migration**
    - [x] 1.1 In `apps/accounts/models.py`, add `campaign_pause_reason = models.CharField(max_length=20, blank=True)`.
    - [x] 1.2 Generate and run migration: `python manage.py makemigrations accounts && python manage.py migrate`.

- [x] 2. **Mailing Engine Exceptions**
    - [x] 2.1 In `apps/mailing/engine.py`, define `QuotaExceededError(Exception)`.
    - [x] 2.2 Update `_send_via_microsoft` to check for `ErrorExceededMessageLimit` and raise `QuotaExceededError`.
    - [x] 2.3 Update `_send_via_gmail` to check for `rateLimitExceeded`, `userRateLimitExceeded`, or `(Mail sending)` and raise `QuotaExceededError`.

- [x] 3. **Task & Signal Handling**
    - [x] 3.1 In `apps/mailing/tasks.py`, refactor `send_relink_notification` to `send_campaign_paused_notification(user_pk, reason)`.
    - [x] 3.2 In `apps/mailing/tasks.py::process_mailing_queue`, set `user.campaign_pause_reason` and call notification for `QuotaExceededError` and `TokenExpiredError`.
    - [x] 3.3 In `apps/accounts/signals.py::pause_campaign_on_unlink`, set `user.campaign_pause_reason = "unlinked"`.

- [x] 4. **Dashboard & UI**
    - [x] 4.1 In `apps/dashboard/views.py::toggle_campaign`, clear `campaign_pause_reason` (set to `""`) on any action.
    - [x] 4.2 In `templates/dashboard/index.html`, add a warning banner block that displays reasoned messages for `expired`, `quota`, and `unlinked`.

- [x] 5. **Validation & Testing**
    - [x] 5.1 Create tests in `apps/mailing/tests/test_pause_notifications.py` to verify error detection and state persistence.
    - [x] 5.2 Verify UI banner appearance by manually mocking the reason in the DB (staff check).
