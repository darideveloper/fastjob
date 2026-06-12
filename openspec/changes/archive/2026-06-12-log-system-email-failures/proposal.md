## Why

Currently, transactional system emails in production (such as welcome, account deleted, OAuth linked, and low-credits warning emails) fail silently when SMTP issues or credential configuration problems occur. This is because these emails call Django's `.send(fail_silently=True)`, which suppresses exceptions internally. Consequently, the surrounding `try/except` blocks are never executed, and no logs or Sentry error events are generated, making it impossible to detect and diagnose email dispatch failures.

## What Changes

- Modify all system email task dispatch calls to execute with `fail_silently=False` (or use Django's default non-silent behavior).
- Ensure all transactional system email tasks are wrapped in robust `try/except` blocks.
- Upgrade failure logs from `WARNING` to `ERROR` level and pass `exc_info=True` to output full stack trace details to the console and allow auto-reporting to Sentry.
- Ensure celery task execution handles these failures cleanly at the task level so that transient errors do not trigger infinite celery task retries or unhandled crashes.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `mailing`: Update specifications to require non-silent sending and error-level logging (with tracebacks) for campaign pause notifications and low-credits warning alerts.
- `accounts`: Update specifications to require non-silent sending and error-level logging (with tracebacks) for welcome, account deleted, and OAuth linked emails.
- `payments`: Update specifications to require error-level logging (with tracebacks) for payment receipt email sending failures.

## Impact

- Modifies tasks in `apps/accounts/tasks.py`, `apps/mailing/tasks.py`, and `apps/payments/tasks.py`.
- No database migrations, external package upgrades, or breaking API changes are required.
