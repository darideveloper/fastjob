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

