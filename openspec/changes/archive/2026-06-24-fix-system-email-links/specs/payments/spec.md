## MODIFIED Requirements

### Requirement: Payment Receipt Email

When a Stripe payment is completed (`checkout.session.completed` webhook), the system MUST send a branded receipt email to the user via a Celery task (`send_payment_receipt_email`). The email MUST use the branded email layout and MUST include:

1. A clear subject in Spanish: "FastJob: Confirmación de tu compra de {N} envíos" where `{N}` is the number of credits granted.
2. The package name and price paid (e.g., "50 envíos — 9,99 €").
3. The number of credits granted.
4. The user's updated total balance (`credits_remaining` after the grant).
5. A link to the Stripe billing portal whose URL MUST resolve to the `billing_portal` view (currently mounted at `/payments/portal/`) for invoice access.
6. A link to the dashboard (`/dashboard/`).

The task MUST receive `user.pk` and `StripePayment.pk` as arguments so it can look up fresh data. The task MUST handle the case where the user or payment no longer exists (log and return silently). Errors in sending MUST be logged at ERROR level with a full stack trace (`exc_info=True`) to allow Sentry integration to capture it, and MUST NOT affect the credit-granting flow. The URLs embedded in the email MUST be constructed via `apps.core.urls.abs_url()` (the single source of truth for absolute system URLs), not by string concatenation, so that route renames cannot silently break the link.

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

#### Scenario: SMTP failure during payment receipt email is logged

- **GIVEN** the SMTP server is unreachable
- **WHEN** `send_payment_receipt_email.delay(user.pk, payment.pk)` executes
- **THEN** the exception is caught and logged at ERROR level with a full stack trace.

#### Scenario: Receipt billing-portal link is reachable by GET

- **GIVEN** the receipt email has been delivered
- **WHEN** the recipient clicks the "Gestionar facturación en Stripe" link
- **THEN** the request method MUST be allowed (the `billing_portal` view MUST NOT require POST).
- **AND** the response MUST be a redirect to a Stripe billing-portal session URL (HTTP 302) or to the dashboard with an error message.

#### Scenario: Receipt links use the abs_url helper

- **GIVEN** the `abs_url()` helper is registered in `apps.core.urls`
- **WHEN** `send_payment_receipt_email` builds the context for the email template
- **THEN** both `billing_url` and `dashboard_url` MUST be produced by calling `abs_url(...)` with the corresponding view names.
- **AND** the resulting URLs MUST equal what `reverse(view_name)` would return when prefixed with the site scheme and domain.

## ADDED Requirements

### Requirement: Billing Portal Is GET-Accessible

The `billing_portal` view in `apps/payments/views.py` MUST be reachable by an HTTP GET request (i.e., MUST NOT be decorated with `@require_POST`). The view MUST continue to be protected by `@login_required`. A GET request MUST be sufficient to look up or create the Stripe customer, create a billing-portal session, and redirect the authenticated user to the session URL.

#### Scenario: GET to billing portal redirects to Stripe
- **WHEN** an authenticated user issues GET `/payments/portal/`
- **THEN** the view returns a 302 redirect to a `https://billing.stripe.com/...` URL.
- **AND** no HTTP 405 is returned.

#### Scenario: Unauthenticated GET to billing portal is rejected
- **WHEN** an anonymous user issues GET `/payments/portal/`
- **THEN** the response is a redirect to the login page (HTTP 302), not a 405.
