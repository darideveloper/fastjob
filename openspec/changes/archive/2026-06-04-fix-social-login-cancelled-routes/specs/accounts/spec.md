## ADDED Requirements

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
