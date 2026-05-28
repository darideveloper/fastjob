## MODIFIED Requirements

### Requirement: Reasoned Campaign Pause Notifications

When a campaign is paused by the system due to a terminal error, the notification sent to the user MUST use the branded email layout (`templates/email/base.html`) and MUST be sent as an `EmailMultiAlternatives` message with both plain-text and HTML alternatives. The HTML alternative MUST include the FastJob logo, a colored header, and the standard footer. The plain-text body MUST contain the same informational content as the HTML alternative without markup.

A notification MUST also be sent when the CV file is unavailable or when the user's OAuth account is disconnected.

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

- **GIVEN** a campaign is paused because the active CV file could not be read from storage
- **THEN** the email sent MUST specify that the CV file is no longer available and the user should upload a new CV from the dashboard.
- **AND** the HTML alternative MUST use the branded email layout with logo, header, and footer.

### Requirement: Branded Email Layout

All outgoing emails from FastJob — both system notifications and CV campaign emails — MUST be wrapped in a shared HTML email layout template (`templates/email/base.html`) that provides consistent branding across all communications. The layout MUST include:

1. A header section with the FastJob logo (sourced from `SystemSettings.email_logo_url`, defaulting to `https://raw.githubusercontent.com/darideveloper/fastjob/refs/heads/main/static/images/fastjob-logo.png`).
2. A content area where the email-specific body is injected.
3. A footer section with the text from `SystemSettings.email_footer_text` (defaulting to `"© 2026 FastJob. Todos los derechos reservados."`) and links to privacy/terms pages.

The layout MUST use inline CSS styles (no `<link>` or external stylesheets) for email-client compatibility. The primary accent color MUST be read from `SystemSettings.email_brand_color` (defaulting to `#007BFF`).

The layout MUST render correctly in Gmail (web + app), Outlook (desktop + web), Apple Mail, and Microsoft Graph clients.

#### Scenario: CV outbound email uses branded layout

- **GIVEN** an active campaign sending a CV email
- **WHEN** `send_cv_email` renders the email
- **THEN** the final HTML body MUST be the content from `EmailTemplate.render()` wrapped inside the branded email layout with logo, header, and footer.

#### Scenario: Campaign-paused notification uses branded layout

- **GIVEN** a campaign-paused notification is dispatched
- **WHEN** `send_campaign_paused_notification` renders the HTML alternative
- **THEN** the HTML MUST include the branded layout with logo, header, and footer.

#### Scenario: Logo URL is overridden by admin

- **GIVEN** an admin sets `SystemSettings.email_logo_url` to `https://cdn.example.com/logo.png`
- **WHEN** any branded email is rendered
- **THEN** the `<img>` tag in the header MUST reference `https://cdn.example.com/logo.png` instead of the default.

#### Scenario: Brand color is overridden by admin

- **GIVEN** an admin sets `SystemSettings.email_brand_color` to `#FF6600`
- **WHEN** any branded email is rendered
- **THEN** all accent-colored elements (header background, CTA buttons, links) MUST use `#FF6600` instead of the default `#007BFF`.

#### Scenario: Plain-text fallback is provided alongside HTML

- **GIVEN** any system or campaign email is sent
- **WHEN** the email is dispatched
- **THEN** both a plain-text and an HTML alternative MUST be included in the message so that email clients without HTML support display the content correctly.

## ADDED Requirements

### Requirement: Low-Credits Warning Email

The system MUST send a warning email to the user when their `credits_remaining` drops to or below `SystemSettings.low_credits_threshold` (default `0`). The email MUST be a one-shot notification: it fires at most once per threshold crossing. To avoid re-sending on every campaign tick, the system MUST track `last_low_credits_warning_at` on the User model. A new warning MUST NOT be sent until the user purchases more credits and their balance drops below the threshold again.

The email MUST use the branded email layout and MUST include:
- The user's current credit balance.
- A link to the pricing page (`/payments/paquetes/`) to purchase more credits.
- A clear subject line in Spanish (e.g., "FastJob: Te quedan pocos envíos").

The warning MUST be triggered from `process_mailing_queue` when the user's `credits_remaining` (after decrement) falls to or below `low_credits_threshold`, and MUST NOT be triggered before the decrement (the warning is about the post-send balance). The check and enqueue MUST be atomic with the credit decrement to prevent two concurrent ticks from both enqueuing the warning for the same threshold crossing: the task MUST set `user.last_low_credits_warning_at` immediately using an `F()`-based atomic update (`User.objects.filter(pk=user.pk, last_low_credits_warning_at__isnull=True).update(last_low_credits_warning_at=timezone.now())`) and only enqueue the email task if the update affected exactly one row.

#### Scenario: User hits zero credits and receives warning

- **GIVEN** `SystemSettings.low_credits_threshold` is `0`
- **AND** a user with `credits_remaining = 1` sends a CV email
- **WHEN** the decrement sets `credits_remaining` to `0`
- **THEN** the atomic `last_low_credits_warning_at` update succeeds (one row affected)
- **AND** `send_low_credits_warning.delay(user.pk)` is enqueued
- **AND** the user receives an email stating they have `0` envíos remaining with a link to purchase more.

#### Scenario: Concurrent ticks do not enqueue duplicate warnings

- **GIVEN** two concurrent workers process the same user's mailing queue entry
- **AND** both observe `credits_remaining` at or below `low_credits_threshold`
- **WHEN** both attempt the atomic `last_low_credits_warning_at` update
- **THEN** only the first `WHERE last_low_credits_warning_at IS NULL` update affects a row
- **AND** the second update affects zero rows and does NOT enqueue the warning task.

#### Scenario: Warning is one-shot per threshold crossing

- **GIVEN** a user received a low-credits warning on Monday
- **AND** they have not purchased any credits since
- **WHEN** `process_mailing_queue` evaluates the same user on Tuesday
- **THEN** no second warning email is sent (because `last_low_credits_warning_at` is still set).

#### Scenario: Warning fires again after repurchase

- **GIVEN** a user received a low-credits warning on Monday
- **AND** they purchase 50 credits on Tuesday
- **AND** their credits drop back to `0` on Friday
- **WHEN** `process_mailing_queue` decrements credits to `0` on Friday
- **THEN** a new warning email is sent (because the repurchase reset `last_low_credits_warning_at`).

#### Scenario: Custom threshold fires earlier

- **GIVEN** `SystemSettings.low_credits_threshold` is `5`
- **WHEN** a user's credits drop from `6` to `5`
- **THEN** the warning email is sent at `5` credits, not at `0`.

### Requirement: EmailTemplate Body Wrapped in Branded Layout

`EmailTemplate.render()` MUST continue to return only the content-specific HTML (the user's campaign body). The branded email layout MUST be applied by a new helper function `render_branded_email(subject, body_html, context)` that wraps the rendered `body_html` inside the shared layout template. `send_cv_email` MUST call this helper before passing the final HTML to the Gmail/Graph send functions.

This separation ensures that `EmailTemplate.body_html` remains content-only (editable by admins via Django admin) while the branding chrome is applied consistently and cannot be accidentally removed from individual templates.

#### Scenario: Send path applies branded layout

- **GIVEN** an `EmailTemplate` whose rendered `body_html` is `<p>Hola {company_name}</p>`
- **WHEN** `send_cv_email` processes the email
- **THEN** the final HTML delivered to the Gmail/Graph API MUST contain the `body_html` content wrapped inside the branded layout, with the logo, header, and footer present.
- **AND** the `{company_name}` placeholder MUST be resolved before the wrapping is applied.

#### Scenario: Admin-edited template content is not affected by layout

- **GIVEN** an admin edits `EmailTemplate.body_html` to change the greeting text
- **WHEN** the email is sent
- **THEN** the layout chrome (logo, colors, footer) is identical to all other emails, regardless of the content change.

### Requirement: SystemSettings Email Branding Fields

`SystemSettings` (`apps/mailing/models.py`) SHALL expose the following fields for configurable email branding:

| Field | Type | Default | verbose_name |
|---|---|---|---|
| `email_logo_url` | `URLField` | `https://raw.githubusercontent.com/darideveloper/fastjob/refs/heads/main/static/images/fastjob-logo.png` | `"URL del logo en emails"` |
| `email_brand_color` | `CharField(7)` | `#007BFF` | `"Color de marca en emails"` |
| `email_footer_text` | `TextField` | `"© 2026 FastJob. Todos los derechos reservados."` | `"Texto del pie de email"` |
| `low_credits_threshold` | `IntegerField` | `0` | `"Umbral de aviso de envíos bajos"` |

All fields MUST have Spanish verbose names. A Django migration MUST be created to add the columns with their defaults. `low_credits_threshold` MUST be non-negative (`validators.MinValueValidator(0)`). `email_brand_color` MUST validate as a 7-character hex color string starting with `#`.

#### Scenario: Admin customizes email branding

- **GIVEN** a staff user opens `/admin/mailing/systemsettings/1/change/`
- **WHEN** they set `email_logo_url` to `https://cdn.example.com/logo.png`, `email_brand_color` to `#FF6600`, and `email_footer_text` to `"Mi empresa S.L."`
- **THEN** all subsequent branded emails MUST reflect these values.

#### Scenario: Default branding is used on fresh install

- **GIVEN** a freshly seeded database with no manual admin configuration
- **WHEN** `SystemSettings.get()` is read
- **THEN** `email_logo_url` defaults to the GitHub raw URL, `email_brand_color` defaults to `#007BFF`, and `email_footer_text` defaults to `"© 2026 FastJob. Todos los derechos reservados."`.

#### Scenario: Invalid brand color is rejected

- **GIVEN** a staff user enters `red` in the `email_brand_color` field
- **WHEN** they save the form
- **THEN** a validation error is displayed indicating the value must be a 7-character hex color string starting with `#`.

#### Scenario: Migration adds columns without data loss

- **WHEN** the migration is applied on an existing database
- **THEN** all existing `SystemSettings` rows gain the four new columns with their default values.
- **AND** no existing field values are altered.

### Requirement: User Model Tracks Low-Credits Warning

The `User` model (`apps/accounts/models.py`) SHALL gain a nullable `DateTimeField` `last_low_credits_warning_at` (default `None`, verbose name `"Último aviso de envíos bajos"`). This field tracks when the most recent low-credits warning email was sent to the user. It MUST be reset to `None` when the user purchases credits (i.e., when `total_purchased_credits` is incremented in `_handle_successful_payment`).

#### Scenario: Field is set when warning is sent

- **GIVEN** a user receives a low-credits warning email
- **WHEN** the task completes
- **THEN** `user.last_low_credits_warning_at` MUST be set to the current timestamp.

#### Scenario: Field is reset after repurchase

- **GIVEN** a user with `last_low_credits_warning_at` set
- **WHEN** `_handle_successful_payment` processes their Stripe payment
- **THEN** `last_low_credits_warning_at` MUST be reset to `None`.

#### Scenario: Migration adds field without data loss

- **WHEN** the migration is applied on an existing database
- **THEN** all existing `User` rows gain `last_low_credits_warning_at = NULL`.
- **AND** no existing field values are altered.