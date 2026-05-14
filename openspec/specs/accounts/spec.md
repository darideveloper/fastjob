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

