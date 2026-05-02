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

