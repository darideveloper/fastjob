# Tasks: Harden Outlook Integration

- [x] 1. **Mailing Engine Refinement**
    - [x] 1.1 In `apps/mailing/engine.py`, update `_refresh_token_locked` and the preceding "cheap path" to use a 600-second (10-minute) buffer instead of 60 seconds.
    - [x] 1.2 In `apps/mailing/engine.py`, update `_send_via_microsoft` to handle response status codes:
        - [x] 1.2.1 Raise `TokenExpiredError` on 401 and 403.
        - [x] 1.2.2 Raise `TokenRefreshTransientError` on 429 and 5xx.
    - [x] 1.3 Apply similar classification logic to `_send_via_gmail` for parity.

- [x] 2. **Mailing Task Robustness**
    - [x] 2.1 In `apps/mailing/tasks.py`, modify `process_mailing_queue` to find `last_log` by user only, removing the `status=MailingLog.Status.SENT` filter.

- [x] 3. **Validation & Testing**
    - [x] 3.1 Create a reproduction test in `apps/mailing/tests/test_harden_engine.py`:
        - [x] 3.1.1 Verify that a 401 error during Microsoft send pauses the campaign.
        - [x] 3.1.2 Verify that a 429 error during Microsoft send marks the log as FAILED but leaves the campaign active.
        - [x] 3.1.3 Verify that after a failure, the next send attempt respects the `global_send_interval_minutes` (no minute-by-minute retry).
    - [x] 3.2 Run all mailing tests: `pytest apps/mailing/tests/`.
