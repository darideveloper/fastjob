## ADDED Requirements

### Requirement: Payment Receipt Email

When a Stripe payment is completed (`checkout.session.completed` webhook), the system MUST send a branded receipt email to the user via a Celery task (`send_payment_receipt_email`). The email MUST use the branded email layout and MUST include:

1. A clear subject in Spanish: "FastJob: Confirmación de tu compra de {N} envíos" where `{N}` is the number of credits granted.
2. The package name and price paid (e.g., "50 envíos — 9,99 €").
3. The number of credits granted.
4. The user's updated total balance (`credits_remaining` after the grant).
5. A link to the Stripe billing portal (`/payments/billing-portal/`) for invoice access.
6. A link to the dashboard (`/dashboard/`).

The task MUST receive `user.pk` and `StripePayment.pk` as arguments so it can look up fresh data. The task MUST handle the case where the user or payment no longer exists (log and return silently). Errors in sending MUST be logged at WARNING level and MUST NOT affect the credit-granting flow.

#### Scenario: User receives payment receipt after purchase

- **GIVEN** a user purchases the "50 envíos" package for 9,99 €
- **WHEN** `_handle_successful_payment` processes the webhook
- **THEN** `send_payment_receipt_email.delay(user.pk, payment.pk)` is enqueued.
- **AND** the user receives a branded email with subject "FastJob: Confirmación de tu compra de 50 envíos".
- **AND** the email body shows the package name, price, credits granted, total balance, and links to the billing portal and dashboard.

#### Scenario: Receipt email uses branded layout

- **GIVEN** the branded layout template exists
- **WHEN** the payment receipt email is rendered
- **THEN** the HTML alternative MUST include the FastJob logo, brand-colored header, receipt content, and footer.

#### Scenario: User deleted before receipt email is sent

- **GIVEN** a user is deleted between the webhook processing and the Celery task execution
- **WHEN** `send_payment_receipt_email` runs and `User.DoesNotExist` is raised
- **THEN** the task logs a WARNING and returns silently without error.

#### Scenario: Payment not found in receipt task

- **GIVEN** a StripePayment record is deleted before the Celery task runs
- **WHEN** `send_payment_receipt_email` runs and `StripePayment.DoesNotExist` is raised
- **THEN** the task logs a WARNING and returns silently.

### Requirement: Low-Credits Warning Resets After Purchase

`_handle_successful_payment` in `apps/payments/views.py` MUST reset `user.last_low_credits_warning_at` to `None` when credits are granted, so that the user can receive a new low-credits warning if their balance drops below the threshold again.

#### Scenario: Low-credits warning flag is reset after purchase

- **GIVEN** a user with `last_low_credits_warning_at` set to a non-null value
- **WHEN** `_handle_successful_payment` processes their Stripe payment
- **THEN** `User.last_low_credits_warning_at` is set to `None` as part of the atomic update.

#### Scenario: Purchase without prior warning is unaffected

- **GIVEN** a user with `last_low_credits_warning_at = None`
- **WHEN** `_handle_successful_payment` processes their Stripe payment
- **THEN** `last_low_credits_warning_at` remains `None` (no unnecessary write).