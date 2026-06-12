## Context

In production, FastJob uses an SMTP backend for sending transactional emails (such as signup welcomes, deletion notices, low credit alerts, and campaign pause notices). 
Currently, the codebase calls `msg.send(fail_silently=True)` across several Celery tasks. Because Django swallows any SMTP/socket exceptions when `fail_silently=True` is active, the enclosing `try/except Exception as e:` blocks are never triggered. As a result, email sending failures are completely silent, leaving no terminal/console logs and bypassing Sentry issue tracking.

## Goals / Non-Goals

**Goals:**
- Enable exception propagation during system email delivery by using `msg.send(fail_silently=False)` (or omitting the argument, which defaults to `False`).
- Centralize error logging inside the try/except blocks of all transactional email functions, utilizing `logger.error(..., exc_info=True)` to record full tracebacks.
- Ensure that Sentry captures all SMTP/email-sending failures in production automatically by raising logs to the `ERROR` level.

**Non-Goals:**
- This design does NOT cover the OAuth2 campaign email engine (`send_cv_email`), which already has detailed database-level and standard logging.
- We will NOT change the globally configured `EMAIL_BACKEND` or write custom Django email backend wrapper classes.
- We will NOT let exceptions bubble out of Celery tasks, to prevent unwanted task crash/retry loops on transient network errors.

## Decisions

### Decision D1: Task-Level Logging over custom Email Backend wrapper
- **Choice**: Modify each transactional task individually instead of wrapping the email backend.
- **Rationale**: Task-level logging gives us direct access to application-specific variables (e.g., `user_pk`, `provider_name`, `payment_pk`). This lets us emit logs with rich context, making troubleshooting much easier. A generic email backend wrapper lacks this granular task/user context.

### Decision D2: Upgrade logs to ERROR level with `exc_info=True`
- **Choice**: Convert warnings to errors and log the exception traceback.
- **Rationale**: Sentry is configured to capture logs at level `ERROR` and higher. Emitting error logs with `exc_info=True` ensures that detailed stack traces are saved to Sentry and printed directly to the production terminal/stdout for Docker/PaaS environment tools to collect.

### Decision D3: Catch exceptions and exit tasks cleanly
- **Choice**: Catch the exceptions inside each task and do not re-raise them.
- **Rationale**: If we let the exception bubble up, Celery might mark the task as failed or retry it automatically. Since SMTP failures can be terminal (e.g., bad email address), we swallow the exception at the end of the block so the task finishes cleanly, but only *after* generating detailed logs.

## Risks / Trade-offs

- **Risk: Logging flood during SMTP downtime** -> If the production SMTP server goes down, every sent system email will log a detailed traceback.
  - *Mitigation*: This is desirable behavior because it triggers alert monitoring in Sentry and console alerts. Sentry groups duplicate exceptions automatically, preventing alert fatigue.
