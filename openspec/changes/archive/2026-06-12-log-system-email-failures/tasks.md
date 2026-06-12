## 1. Accounts Capability Tasks

- [x] 1.1 Update `send_welcome_email` task in `apps/accounts/tasks.py` to change the log level from `WARNING` to `ERROR` and append `exc_info=True`.
- [x] 1.2 Update `send_account_deleted_email` task in `apps/accounts/tasks.py` to remove `fail_silently=True` from `msg.send()`, change log level from `WARNING` to `ERROR`, and append `exc_info=True`.
- [x] 1.3 Update `send_oauth_link_email` task in `apps/accounts/tasks.py` to remove `fail_silently=True` from `msg.send()`, change log level from `WARNING` to `ERROR`, and append `exc_info=True`.

## 2. Mailing Capability Tasks

- [x] 2.1 Update `send_campaign_paused_notification` task in `apps/mailing/tasks.py` to wrap the `msg.send()` call inside a `try/except Exception as e` block, remove `fail_silently=True` from `msg.send()`, and log failures via `logger.error(..., exc_info=True)`.
- [x] 2.2 Update `send_low_credits_warning` task in `apps/mailing/tasks.py` to remove `fail_silently=True` from `msg.send()`, change log level from `WARNING` to `ERROR`, and append `exc_info=True`.

## 3. Payments Capability Tasks

- [x] 3.1 Update `send_payment_receipt_email` task in `apps/payments/tasks.py` to change the log level from `WARNING` to `ERROR` and append `exc_info=True`.

## 4. Verification & Testing

- [x] 4.1 Update `test_welcome_email_failures_logged` in `apps/accounts/tests/test_welcome_email.py` to check for logging at `ERROR` level.
- [x] 4.2 Update `test_receipt_email_missing_user_logs_warning` in `apps/payments/tests/test_payment_email.py` to assert logging at `ERROR` level.
- [x] 4.3 Add a unit test to verify that `send_account_deleted_email` logs failures at `ERROR` level when `msg.send()` fails.
- [x] 4.4 Add a unit test to verify that `send_oauth_link_email` logs failures at `ERROR` level when `msg.send()` fails.
- [x] 4.5 Add a unit test to verify that `send_campaign_paused_notification` logs failures at `ERROR` level when `msg.send()` fails.
- [x] 4.6 Add a unit test to verify that `send_low_credits_warning` logs failures at `ERROR` level when `msg.send()` fails.
- [x] 4.7 Run `pytest` to confirm all unit tests pass successfully.
