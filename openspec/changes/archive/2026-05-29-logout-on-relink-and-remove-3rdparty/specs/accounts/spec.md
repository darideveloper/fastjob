## ADDED Requirements

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
- **WHEN** the code reverses `socialaccount_signup`
- **THEN** it resolves to a URL redirecting to `/accounts/login/`
