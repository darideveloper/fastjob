## MODIFIED Requirements

### Requirement: Reasoned Campaign Pause Notifications

When a campaign is paused by the system due to a terminal error, the notification sent to the user MUST use the branded email layout (`templates/email/base.html`) and MUST be sent as an `EmailMultiAlternatives` message with both plain-text and HTML alternatives. The HTML alternative MUST include the FastJob logo, a colored header, and the standard footer. The plain-text body MUST contain the same informational content as the HTML alternative without markup.

A notification MUST also be sent when the CV file is unavailable or when the user's OAuth account is disconnected. If the email fails to send, the exception MUST be caught and logged at ERROR level with a full stack trace (`exc_info=True`), and the task must exit cleanly without throwing unhandled errors or triggering Celery retries.

#### Scenario: Email for Quota Reached

- **GIVEN** a campaign is paused because of a `QuotaExceededError`
- **THEN** the email sent MUST specify that the **provider-enforced** limit was reached and the user should wait until tomorrow.
- **AND** the HTML alternative MUST use the branded email layout with logo, header, and footer.

#### Scenario: Email for Token Expired

- **GIVEN** a campaign is paused because of a `TokenExpiredError`
- **THEN** the email sent MUST specify that the email session has expired and provide a link to re-link the account.
- **AND** the HTML alternative MUST use the branded email layout with logo, header, and footer.

#### Scenario: Email for OAuth Unlinked

- **GIVEN** a campaign is paused because the user disconnected their OAuth account
- **THEN** the `pause_campaign_on_unlink` signal handler MUST enqueue `send_campaign_paused_notification.delay(user.pk, "unlinked")`
- **AND** the email sent MUST specify that the email account was disconnected and provide a link to re-link the account.
- **AND** the HTML alternative MUST use the branded email layout with logo, header, and footer.

#### Scenario: Email for Missing CV

- **GIVEN** a campaign is paused because of a `CVFileMissingError`
- **THEN** the email sent MUST specify that the CV file is missing and provide advice to re-upload it.
- **AND** the HTML alternative MUST use the branded email layout with logo, header, and footer.

#### Scenario: SMTP failure during campaign pause email is logged

- **GIVEN** the SMTP server is unreachable
- **WHEN** `send_campaign_paused_notification.delay(user.pk, "expired")` executes
- **THEN** the exception is caught and logged at ERROR level with a full stack trace.

---

### Requirement: Low-Credits Warning Email

The system MUST send a warning email to the user when their `credits_remaining` drops to or below `SystemSettings.low_credits_threshold` (default `0`). The email MUST be a one-shot notification: it fires at most once per threshold crossing. To avoid re-sending on every campaign tick, the system MUST track `last_low_credits_warning_at` on the User model. A new warning MUST NOT be sent until the user purchases more credits and their balance drops below the threshold again.

The email MUST use the branded email layout and MUST include:
- The user's current credit balance.
- A link to the pricing page (`/payments/paquetes/`) to purchase more credits.
- A clear subject line in Spanish (e.g., "FastJob: Te quedan pocos envíos").

The warning MUST be triggered from `process_mailing_queue` when the user's `credits_remaining` (after decrement) falls to or below `low_credits_threshold`, and MUST NOT be triggered before the decrement (the warning is about the post-send balance). The check and enqueue MUST be atomic with the credit decrement to prevent two concurrent ticks from both enqueuing the warning for the same threshold crossing: the task MUST set `user.last_low_credits_warning_at` immediately using an `F()`-based atomic update (`User.objects.filter(pk=user.pk, last_low_credits_warning_at__isnull=True).update(last_low_credits_warning_at=timezone.now())`) and only enqueue the email task if the update affected exactly one row.

If the warning email fails to send, the error MUST be raised from Django's email engine (via default `fail_silently=False` behavior), caught at the task level, and logged at ERROR level with a full stack trace (`exc_info=True`) to allow Sentry integration to capture it, without raising unhandled exceptions.

#### Scenario: User hits zero credits and receives warning

- **GIVEN** `SystemSettings.low_credits_threshold` is `0`
- **AND** a user with `credits_remaining = 1` sends a CV email
- **WHEN** the decrement sets `credits_remaining` to `0`
- **THEN** the atomic `last_low_credits_warning_at` update succeeds (one row affected)
- **AND** `send_low_credits_warning.delay(user.pk)` is enqueued
- **AND** the user receives an email stating they have `0` envíos remaining with a link to purchase more.

#### Scenario: Concurrent ticks do not enqueue duplicate warnings

- **GIVEN** two concurrent ticks run for the same user
- **AND** both observe `credits_remaining` at or below `low_credits_threshold`
- **WHEN** both attempt the atomic `last_low_credits_warning_at` update
- **THEN** only the first `WHERE last_low_credits_warning_at IS NULL` update affects a row
- **AND** only one task `send_low_credits_warning.delay(user.pk)` is enqueued.

#### Scenario: SMTP failure during low-credits email is logged

- **GIVEN** the SMTP server is unreachable
- **WHEN** `send_low_credits_warning.delay(user.pk)` executes
- **THEN** the exception is caught and logged at ERROR level with a full stack trace.
