## MODIFIED Requirements

### Requirement: Welcome Email on Signup

The system MUST send a branded welcome email to every new user when the `user_signed_up` signal fires. The email MUST be dispatched via a Celery task (`send_welcome_email`) to avoid blocking the signup flow. The email MUST use the branded email layout and MUST include:

1. A greeting using the user's first name (falling back to their email if `first_name` is empty).
2. A summary of their signup bonus (`initial_free_credits` from `SystemSettings`).
3. Onboarding instruction to upload a CV and start their campaign.
4. A link to `/dashboard/` for CV upload and campaign start.
5. Subject line in Spanish: "¡Bienvenido/a a FastJob! Tus {N} envíos gratis te esperan" where `{N}` is the signup credit count.

The Celery task MUST NOT fail the signup flow if the email cannot be sent. Errors MUST be raised from Django's email engine (via default `fail_silently=False` behavior), caught at the task level, and logged at ERROR level with a full stack trace (`exc_info=True`) to allow Sentry integration to capture them.

#### Scenario: New user receives welcome email

- **GIVEN** `SystemSettings.initial_free_credits` is `5`
- **WHEN** a new user signs up via OAuth
- **THEN** `send_welcome_email.delay(user.pk)` is enqueued from the `user_signed_up` signal handler.
- **AND** the user receives an email with subject "¡Bienvenido/a a FastJob! Tus 5 envíos gratis te esperan".
- **AND** the email body mentions the 5 free credits and links to `/dashboard/`.

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

## REMOVED Requirements

### Requirement: OAuth Link Confirmation Email

**Reason**: Users sign up and log in exclusively using Google or Microsoft OAuth. They cannot manually link or unlink accounts from their profile, making a separate "OAuth account linked" email notification redundant.
**Migration**: Disconnect or remove the `notify_oauth_link` signal handler to avoid sending redundant emails during first-time social signup.
