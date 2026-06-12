## MODIFIED Requirements

### Requirement: Welcome Email on Signup

The system MUST send a branded welcome email to every new user when the `user_signed_up` signal fires. The email MUST be dispatched via a Celery task (`send_welcome_email`) to avoid blocking the signup flow. The email MUST use the branded email layout and MUST include:

1. A greeting using the user's first name (falling back to their email if `first_name` is empty).
2. A summary of their signup bonus (`initial_free_credits` from `SystemSettings`).
3. Three onboarding steps: upload a CV, link your email account (Google/Microsoft), and start your campaign.
4. Links to each step: `/dashboard/` for CV upload and campaign start; `/accounts/3rdparty/` for linking an email provider.
5. Subject line in Spanish: "¡Bienvenido/a a FastJob! Tus {N} envíos gratis te esperan" where `{N}` is the signup credit count.

The Celery task MUST NOT fail the signup flow if the email cannot be sent. Errors MUST be raised from Django's email engine (via default `fail_silently=False` behavior), caught at the task level, and logged at ERROR level with a full stack trace (`exc_info=True`) to allow Sentry integration to capture them.

#### Scenario: New user receives welcome email

- **GIVEN** `SystemSettings.initial_free_credits` is `5`
- **WHEN** a new user signs up via OAuth
- **THEN** `send_welcome_email.delay(user.pk)` is enqueued from the `user_signed_up` signal handler.
- **AND** the user receives an email with subject "¡Bienvenido/a a FastJob! Tus 5 envíos gratis te esperan".
- **AND** the email body mentions the 5 free credits and links to `/dashboard/` and `/accounts/3rdparty/`.

#### Scenario: Welcome email uses branded layout

- **GIVEN** the branded layout template exists
- **WHEN** the welcome email is rendered
- **THEN** the HTML alternative MUST include the FastJob logo, brand-colored header, onboarding content, and footer with the configured footer text.

#### Scenario: SMTP failure does not block signup

- **GIVEN** the SMTP server is unreachable
- **WHEN** `send_welcome_email.delay(user.pk)` executes
- **THEN** the user's account is still created successfully.
- **AND** the error is caught and logged at ERROR level with full traceback.
- **AND** `user.credits_remaining` is still set to the signup bonus value.

#### Scenario: User without first name shows email in greeting

- **GIVEN** a new user whose `first_name` is empty and `email` is `ana@example.com`
- **WHEN** the welcome email is sent
- **THEN** the greeting uses "Hola, ana@example.com" instead of a blank name.

---

### Requirement: Account Deletion Confirmation Email

The `delete_account` view (`apps/dashboard/views.py`) MUST send a branded confirmation email to the user's address **before** the user record is destroyed. The email MUST be dispatched synchronously (not via Celery) because the user record will not exist by the time a Celery worker picks up the task. The email MUST use the branded email layout and MUST include:

1. A clear subject in Spanish: "FastJob: Tu cuenta ha sido eliminada".
2. A confirmation that all personal data (CV files, mailing logs, campaign settings) has been removed.
3. A note that Stripe payment records are retained for accounting purposes (per GDPR, financial records are a legitimate basis for retention).
4. A link to the homepage `/` in case they want to re-register.

The email MUST be sent before `user.delete()` so that `user.email` is still available. If the email fails to send, deletion MUST still proceed (non-blocking). The sending operation MUST use `fail_silently=False` (default behavior), and any exceptions raised MUST be caught and logged at ERROR level with a full stack trace (`exc_info=True`).

#### Scenario: User receives deletion confirmation email

- **GIVEN** a user confirms deletion by typing their email
- **WHEN** `delete_account` processes the POST request
- **THEN** a confirmation email is sent to `user.email` before `user.delete()` is called.
- **AND** the email uses the branded layout with subject "FastJob: Tu cuenta ha sido eliminada".

#### Scenario: Email failure does not block deletion

- **GIVEN** the SMTP server is unreachable
- **WHEN** `delete_account` attempts to send the confirmation email
- **THEN** the error is caught and logged at ERROR level with full traceback.
- **AND** the user account is still deleted successfully.

---

### Requirement: OAuth Link Confirmation Email

When a user successfully links a social account (Google or Microsoft), the system MUST send a branded confirmation email to the user. The email MUST be dispatched via a Celery task from the `social_account_added` signal provided by allauth (which fires only when a new `SocialAccount` is created, not on updates). The email MUST use the branded email layout and MUST include:

1. The provider name in Spanish (Google / Microsoft).
2. A confirmation that the account is now linked and ready to send CV emails.
3. A link to `/dashboard/` to start the campaign.
4. Subject line in Spanish: "FastJob: Tu cuenta de {provider} ha sido vinculada".

This email MUST NOT fire when a user disconnects (unlinks) a provider — the existing `social_account_removed` signal handles pausing the campaign and sending the "unlinked" notification. If the email fails to send, the exception MUST be caught and logged at ERROR level with a full stack trace (`exc_info=True`) to allow Sentry integration to capture it, and it MUST NOT crash the background worker or trigger automatic Celery task retries.

#### Scenario: User links Google account and receives confirmation

- **GIVEN** a user links their Google account via OAuth
- **WHEN** the `SocialAccount` is created
- **THEN** `send_oauth_link_email.delay(user.pk, "Google")` is enqueued.
- **AND** the user receives an email confirming their Google account is linked.

#### Scenario: User links Microsoft account and receives confirmation

- **GIVEN** a user links their Microsoft account via OAuth
- **WHEN** the `SocialAccount` is created
- **THEN** `send_oauth_link_email.delay(user.pk, "Microsoft")` is enqueued.
- **AND** the user receives an email confirming their Microsoft account is linked.

#### Scenario: Unlink does not trigger link confirmation

- **GIVEN** a user disconnects their Google account
- **WHEN** the `social_account_removed` signal fires
- **THEN** no link confirmation email is sent.
- **AND** the existing campaign-paused notification for "unlinked" IS sent (per the existing spec).

#### Scenario: SMTP failure during link confirmation email is logged

- **GIVEN** the SMTP server is unreachable
- **WHEN** `send_oauth_link_email.delay(user.pk, "Google")` executes
- **THEN** the exception is caught and logged at ERROR level with a full stack trace.
