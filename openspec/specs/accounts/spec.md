# accounts Specification

## Purpose
TBD - created by archiving change add-mobile-responsive-layout. Update Purpose after archive.
## Requirements
### Requirement: Login page renders successfully without an HTTP 500
`GET /accounts/login/` SHALL return HTTP 200 for an anonymous client. The C3 OAuth-only URL hardening (which omits the password / signup / email-management subset of `allauth.urls`) MUST be preserved — no signup form, password-reset endpoint, or password-change endpoint is to be mounted as part of fixing this regression.

The current failure mode is `NoReverseMatch: Reverse for 'account_signup' not found` raised inside `allauth.account.views.LoginView.get_context_data()` when it calls `reverse('account_signup')` to populate the template context. The fix is to register the URL **name** `account_signup` against a `RedirectView` that bounces to `account_login`, so the reverse lookup succeeds and the rendered template (which already does not link to a signup form) is unchanged.

#### Scenario: Anonymous GET /accounts/login/ returns 200
- **GIVEN** an anonymous Django test client
- **WHEN** the client issues `GET /accounts/login/`
- **THEN** the response status code is 200
- **AND** the response is rendered from `templates/account/login.html`
- **AND** no `NoReverseMatch` is raised

#### Scenario: GET /accounts/signup/ redirects to login
- **GIVEN** an anonymous Django test client
- **WHEN** the client issues `GET /accounts/signup/` (the URL associated with the `account_signup` name)
- **THEN** the response status code is 302
- **AND** the `Location` header points to `/accounts/login/`
- **AND** following the redirect yields HTTP 200 from the login template

#### Scenario: C3 OAuth-only posture preserved
- **GIVEN** the project's `config/urls.py` is loaded
- **WHEN** any of the following URL names are reversed: `account_signup`, `account_login`, `account_logout`
- **THEN** the reverses succeed
- **AND** none of the following URL names is registered (verified via `urls.get_resolver().reverse_dict`): `account_set_password`, `account_change_password`, `account_reset_password`, `account_email`, `account_inactive`, `account_confirm_email`

### Requirement: Styled Logout Confirmation
The logout confirmation page (`/accounts/logout/`) MUST be styled with the project's brand identity. It MUST provide a clear confirmation message and a prominent action button to proceed with the logout.

#### Scenario: User clicks logout
- **GIVEN** an authenticated user
- **WHEN** they navigate to `/accounts/logout/`
- **THEN** the response status code is 200
- **AND** the page is rendered using `templates/account/logout.html`
- **AND** the content is contained within a centered Tailwind card
- **AND** a "Cerrar sesión" button is present and styled with the brand color.

### Requirement: Social Authentication Configuration
Social authentication credentials (Client ID and Secret) SHALL NOT be stored in static configuration files or environment variables after the initial migration. They MUST be managed via the `SocialApp` database model.

#### Scenario: Login flow uses database credentials
- **GIVEN** `SOCIALACCOUNT_PROVIDERS` in `settings.py` does not contain an `APP` dictionary.
- **AND** a valid `SocialApp` record exists in the database.
- **WHEN** a user initiates a social login (e.g., Google).
- **THEN** `django-allauth` MUST retrieve the credentials from the database.
- **AND** the login flow MUST proceed successfully.

#### Scenario: Settings based credentials removed
- **GIVEN** the migration is complete.
- **WHEN** inspecting `config/settings.py`.
- **THEN** the `SOCIALACCOUNT_PROVIDERS` dictionary MUST NOT contain sensitive `client_id` or `secret` keys.

### Requirement: Persist OAuth Tokens for Background Mailing
The system MUST explicitly configure `django-allauth` to store OAuth tokens in the database (`SOCIALACCOUNT_STORE_TOKENS = True`). This ensures the background mailing engine can retrieve the `SocialToken` required to send emails on the user's behalf via the Gmail/Microsoft Graph APIs.

#### Scenario: Background engine has access to saved tokens
- **GIVEN** `SOCIALACCOUNT_STORE_TOKENS` is `True`
- **WHEN** a user completes the OAuth login flow
- **THEN** their `SocialToken` is saved to the database
- **AND** the mailing engine's `_get_social_token(user)` successfully retrieves it without throwing a `TokenExpiredError: No OAuth token found.`

### Requirement: Track Lifetime Purchased Credits
The `User` model MUST track the lifetime total of credits purchased via Stripe to support multiplier-based limits.
- This field `total_purchased_credits` MUST be updated whenever a `StripePayment` reaches `COMPLETED` status.
- It MUST NOT include free signup bonuses or manual adjustments.

#### Scenario: Payment completion increments lifetime total
- **GIVEN** a user with `total_purchased_credits = 50`.
- **WHEN** a new payment for 100 credits is completed.
- **THEN** `total_purchased_credits` MUST be updated to `150`.

### Requirement: Visible Credit Balance
The `User` model MUST provide a sanitized credit balance for UI display that hides negative values resulting from the hidden multiplier.
- The property `visible_credits` MUST return `max(0, credits_remaining)`.
- All public-facing dashboard and navbar elements MUST use this property instead of the raw `credits_remaining`.

#### Scenario: Negative balance is hidden in UI
- **GIVEN** a user with `credits_remaining = -3`.
- **WHEN** the `visible_credits` property is accessed.
- **THEN** it MUST return `0`.

### Requirement: Unified auth-card chrome across login, logout, and socialaccount screens
The templates `account/login.html`, `account/logout.html`, `socialaccount/authentication_error.html`, `socialaccount/login_cancelled.html`, `socialaccount/connections.html`, and `socialaccount/signup.html` SHALL each render their primary content inside a single centered card on the `brand.bg` page background. The card SHALL use the shared chrome (`bg-white border border-brand-muted rounded-2xl shadow-sm p-6 sm:p-8`), MUST be horizontally centered (`mx-auto`), and MUST cap its width at `max-w-md` on viewports `< lg` and `max-w-lg` at `lg` and above. The FastJob logo (the same `<picture>` asset used by `base.html`'s navbar) SHALL appear above the card title, rendered with `class="h-12 w-auto"` so the rendered height anchors layout and width follows the asset's intrinsic 2.72 : 1 ratio.

`account/login.html` already provides the card chrome (`border-gray-100`); the apply stage migrates the border class to `border-brand-muted` and inserts the logo `<picture>` above the existing `<h1>Bienvenido a FastJob</h1>`.

#### Scenario: Login page uses the unified card chrome
- **GIVEN** an anonymous visitor on `/accounts/login/`
- **WHEN** the page is rendered
- **THEN** the OAuth provider chooser is contained within a single centered card whose classes resolve to `bg-white`, `border-brand-muted`, `rounded-2xl`, `shadow-sm`
- **AND** the FastJob logo `<picture>` is rendered above the card title with `class="h-12 w-auto"`
- **AND** the card is centered horizontally and limited to `max-w-md` at viewport 375 px

#### Scenario: All listed templates share the same chrome
- **WHEN** each of `/accounts/login/`, `/accounts/logout/`, `/accounts/3rdparty/`, and the allauth error/cancelled pages is rendered
- **THEN** each contains a centered card with the same chrome class set (`bg-white border border-brand-muted rounded-2xl shadow-sm`)
- **AND** each renders the FastJob logo above its title

### Requirement: OAuth provider buttons preserve vendor branding
On `account/login.html`, the "Continuar con Google" and "Continuar con Microsoft" buttons MUST NOT be re-skinned in `brand.*` palette colors. Google's button SHALL preserve its existing white-fill / vendor-color-icon / slate-text treatment (matching Google's identity guidelines). Microsoft's button SHALL preserve its existing white-fill / vendor-color-icon / slate-text treatment (matching Microsoft's identity guidelines). The button labels MUST remain exactly `Continuar con Google` and `Continuar con Microsoft` (the existing Spanish copy at `account/login.html:22,33`); they MUST NOT be re-translated to "Sign in with…". Both buttons MUST still meet the WCAG AA contrast and the 44-px touch-target invariant.

#### Scenario: Vendor buttons are not skinned in brand colors
- **WHEN** `/accounts/login/` is rendered
- **THEN** neither the Google nor the Microsoft button has its `background-color` resolved to `brand.DEFAULT`, `brand.dark`, or `brand.cyan`
- **AND** each button renders its vendor-correct color icon (Google "G" in vendor colors; Microsoft squares in vendor colors)
- **AND** each button's label is exactly `Continuar con Google` or `Continuar con Microsoft`
- **AND** each button has computed dimensions ≥ 44 × 44 px at viewport 375 px

### Requirement: Auth error states use brand palette (not semantic red)
The `socialaccount/authentication_error.html` and `socialaccount/login_cancelled.html` templates SHALL convey their state using a Cobalt-leaning icon (`text-brand-dark`) and a slate body (`text-brand-ink`) rather than red. A single primary-fill CTA labelled `Volver a iniciar sesión` SHALL link back to `/accounts/login/`. Semantic red is reserved for destructive intent (e.g. delete account); auth flow errors are framed as recoverable, not destructive.

#### Scenario: Auth-error template renders without semantic red
- **WHEN** `socialaccount/authentication_error.html` is rendered
- **THEN** no element on the page has a computed color or background-color matching the project's semantic red tokens (`bg-red-50`, `bg-red-600`, `text-red-700`, etc.)
- **AND** the page's icon resolves to `brand.dark`
- **AND** a single primary-fill CTA labelled `Volver a iniciar sesión` points to `/accounts/login/`

### Requirement: Spanish verbose names on User fields

The `User` model (`apps/accounts/models.py`) SHALL have explicit Spanish `verbose_name` on every field that previously lacked one.

| Field | verbose_name |
|---|---|
| `is_campaign_active` | `"Campaña activa"` |
| `active_cv` | `"CV activo"` |
| `area_filters` | `"Filtros de sector"` |
| `location_filters` | `"Filtros de localidad"` |
| `stripe_customer_id` | `"ID de cliente Stripe"` |

Fields that already carry a Spanish `verbose_name`
(`credits_remaining`, `total_purchased_credits`, `campaign_pause_reason`)
are unaffected.

The `campaign_pause_reason` field accepts the following values:
`""` (empty, no pause), `"quota"`, `"expired"`, `"unlinked"`, and `"missing_cv"`.

#### Scenario: User change form shows Spanish labels for FastJob fields

- **WHEN** a staff user opens `/admin/accounts/user/<id>/change/`
- **THEN** the FastJob fieldset labels for the five fields above match
  their Spanish verbose names
- **AND** no English auto-generated label is visible

### Requirement: Spanish verbose names on CV fields
All fields of `CV` (`apps/accounts/models.py`) SHALL declare an explicit
`verbose_name` in Spanish.

| Field | verbose_name |
|---|---|
| `user` | `"Usuario"` |
| `file` | `"Archivo"` |
| `name` | `"Nombre"` |
| `created_at` | `"Creado el"` |

#### Scenario: CV change form shows Spanish labels
- **WHEN** a staff user opens `/admin/accounts/cv/<id>/change/`
- **THEN** each field label matches the Spanish string from the table above

### Requirement: UserAdmin FastJob fieldset header is Spanish
`UserAdmin` (`apps/accounts/admin.py`) SHALL use `"Datos FastJob"` as the fieldset header instead of the English string `"FastJob"`.

#### Scenario: User change form shows "Datos FastJob" section header
- **WHEN** a staff user opens `/admin/accounts/user/<id>/change/`
- **THEN** the custom fieldset header reads `"Datos FastJob"`
- **AND** the previous English-only header `"FastJob"` is not rendered

### Requirement: OAuth Unlink Signal Sends Notification

The `pause_campaign_on_unlink` signal handler in `apps/accounts/signals.py` MUST enqueue `send_campaign_paused_notification.delay(user.pk, "unlinked")` after setting `is_campaign_active = False` and `campaign_pause_reason = "unlinked"`, so that users who disconnect their OAuth account receive an explanatory email. This matches the notification pattern used by the `TokenExpiredError` and `QuotaExceededError` handlers in `process_mailing_queue`.

#### Scenario: Disconnecting OAuth account triggers notification email

- **GIVEN** a user with an active campaign and a linked OAuth account
- **WHEN** the user disconnects their OAuth account (triggering `social_account_removed`)
- **THEN** `is_campaign_active` is set to `False`
- **AND** `campaign_pause_reason` is set to `"unlinked"`
- **AND** `send_campaign_paused_notification.delay(user.pk, "unlinked")` is enqueued
- **AND** the user receives an email explaining that their email account was disconnected and providing a link to re-link

### Requirement: Dynamic Initial Credits

The system SHALL allow the administrator to configure the number of free credits granted to new users upon signup. This value MUST be stored in the `SystemSettings` singleton as `initial_free_credits` and default to 5. In addition to granting credits, the `grant_signup_bonus` signal handler MUST enqueue the `send_welcome_email` Celery task so the user receives an onboarding email.

#### Scenario: New user receives dynamic signup bonus and welcome email

- **GIVEN** `SystemSettings.initial_free_credits` is set to 10.
- **WHEN** a new user signs up and the `user_signed_up` signal fires.
- **THEN** the user's `credits_remaining` MUST be set to 10.
- **AND** `total_purchased_credits` MUST remain at 0.
- **AND** `send_welcome_email.delay(user.pk)` MUST be enqueued.

### Requirement: Welcome Email on Signup

The system MUST send a branded welcome email to every new user when the `user_signed_up` signal fires. The email MUST be dispatched via a Celery task (`send_welcome_email`) to avoid blocking the signup flow. The email MUST use the branded email layout and MUST include:

1. A greeting using the user's first name (falling back to their email if `first_name` is empty).
2. A summary of their signup bonus (`initial_free_credits` from `SystemSettings`).
3. Three onboarding steps: upload a CV, link your email account (Google/Microsoft), and start your campaign.
4. Links to each step: `/dashboard/` for CV upload and campaign start; `/accounts/3rdparty/` for linking an email provider.
5. Subject line in Spanish: "¡Bienvenido/a a FastJob! Tus {N} envíos gratis te esperan" where `{N}` is the signup credit count.

The Celery task MUST NOT fail the signup flow if the email cannot be sent. Errors MUST be logged at WARNING level.

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
- **AND** the error is logged at WARNING level.
- **AND** `user.credits_remaining` is still set to the signup bonus value.

#### Scenario: User without first name shows email in greeting

- **GIVEN** a new user whose `first_name` is empty and `email` is `ana@example.com`
- **WHEN** the welcome email is sent
- **THEN** the greeting uses "Hola, ana@example.com" instead of a blank name.

### Requirement: Account Deletion Confirmation Email

The `delete_account` view (`apps/dashboard/views.py`) MUST send a branded confirmation email to the user's address **before** the user record is destroyed. The email MUST be dispatched synchronously (not via Celery) because the user record will not exist by the time a Celery worker picks up the task. The email MUST use the branded email layout and MUST include:

1. A clear subject in Spanish: "FastJob: Tu cuenta ha sido eliminada".
2. A confirmation that all personal data (CV files, mailing logs, campaign settings) has been removed.
3. A note that Stripe payment records are retained for accounting purposes (per GDPR, financial records are a legitimate basis for retention).
4. A link to the homepage `/` in case they want to re-register.

The email MUST be sent before `user.delete()` so that `user.email` is still available. If the email fails to send, deletion MUST still proceed (non-blocking).

#### Scenario: User receives deletion confirmation email

- **GIVEN** a user confirms deletion by typing their email
- **WHEN** `delete_account` processes the POST request
- **THEN** a confirmation email is sent to `user.email` before `user.delete()` is called.
- **AND** the email uses the branded layout with subject "FastJob: Tu cuenta ha sido eliminada".

#### Scenario: Email failure does not block deletion

- **GIVEN** the SMTP server is unreachable
- **WHEN** `delete_account` attempts to send the confirmation email
- **THEN** the error is logged at WARNING level.
- **AND** the user account is still deleted successfully.

### Requirement: OAuth Link Confirmation Email

When a user successfully links a social account (Google or Microsoft), the system MUST send a branded confirmation email to the user. The email MUST be dispatched via a Celery task from the `social_account_added` signal provided by allauth (which fires only when a new `SocialAccount` is created, not on updates). The email MUST use the branded email layout and MUST include:

1. The provider name in Spanish (Google / Microsoft).
2. A confirmation that the account is now linked and ready to send CV emails.
3. A link to `/dashboard/` to start the campaign.
4. Subject line in Spanish: "FastJob: Tu cuenta de {provider} ha sido vinculada".

This email MUST NOT fire when a user disconnects (unlinks) a provider — the existing `social_account_removed` signal handles pausing the campaign and sending the "unlinked" notification.

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

### Requirement: Re-link Action Redirects to Logout View
The warning banner's "Vincular ahora" action button for `"expired"` or `"unlinked"` states SHALL direct the user to the logout confirmation page (`/accounts/logout/`), prompting them to log out so they can log back in and re-establish their OAuth tokens.

#### Scenario: User clicks re-link action
- **GIVEN** an authenticated user on the dashboard with a campaign paused due to expired or unlinked state
- **WHEN** they click the "Vincular ahora" button
- **THEN** the browser redirects them to the logout confirmation page (`/accounts/logout/`)

### Requirement: Social Account Unlinking Disabled
The user SHALL NOT be able to access the social account connections page or manually unlink their Google or Microsoft accounts from the client dashboard.

#### Scenario: Navigating to connections page returns 404
- **WHEN** a user attempts to access `/accounts/3rdparty/` or `/accounts/3rdparty/connections/`
- **THEN** the server returns an HTTP 404 status code (Not Found)

### Requirement: Social Account Signup Defensive Redirect
The name `socialaccount_signup` MUST resolve and redirect to `/accounts/login/` to prevent internal django-allauth library exceptions.

#### Scenario: Reversing socialaccount_signup returns a valid redirect view
- WHEN the code reverses `socialaccount_signup`
- THEN it resolves to a URL redirecting to `/accounts/login/`

### Requirement: Microsoft Identity Association
The system MUST serve the Microsoft identity association JSON file at the `/.well-known/microsoft-identity-association.json` endpoint. This file validates the application's domain ownership for Microsoft OAuth integrations. The endpoint MUST return a JSON response with the `application/json` content type containing the FastJob Microsoft `applicationId` in the `associatedApplications` array.

#### Scenario: Validating Microsoft Identity Association endpoint
- **GIVEN** an anonymous client
- **WHEN** the client issues a `GET` request to `/.well-known/microsoft-identity-association.json`
- **THEN** the response status code is `200 OK`
- **AND** the `Content-Type` header is `application/json`
- **AND** the response body contains `{"associatedApplications": [{"applicationId": "3853b95b-027f-4c59-94e4-d697b2a603a9"}]}`


### Requirement: Social login cancelled and error routing
The system SHALL register the named URL patterns `socialaccount_login_cancelled` and `socialaccount_login_error` to ensure that OAuth cancellation and authentication error flows can resolve successfully and render their corresponding views.

#### Scenario: Reversing socialaccount_login_cancelled
- WHEN the named URL `socialaccount_login_cancelled` is reversed
- THEN it SHALL return `/accounts/social/login/cancelled/`
- AND resolving that path SHALL point to the `login_cancelled` view function or view class

#### Scenario: Reversing socialaccount_login_error
- WHEN the named URL `socialaccount_login_error` is reversed
- THEN it SHALL return `/accounts/social/login/error/`
- AND resolving that path SHALL point to the `login_error` view function or view class


