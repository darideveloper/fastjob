# accounts Specification Delta

## ADDED Requirements

### Requirement: Styled Logout Confirmation
The logout confirmation page (`/accounts/logout/`) MUST be styled with the project's brand identity. It MUST provide a clear confirmation message and a prominent action button to proceed with the logout.

#### Scenario: User clicks logout
- **GIVEN** an authenticated user
- **WHEN** they navigate to `/accounts/logout/`
- **THEN** the response status code is 200
- **AND** the page is rendered using `templates/account/logout.html`
- **AND** the content is contained within a centered Tailwind card
- **AND** a "Cerrar sesión" button is present and styled with the brand color.

### Requirement: Styled Social Account Pages
All social authentication edge-case pages (signup, connections, errors) MUST be styled to match the login page.

#### Scenario: Social signup requires confirmation
- **GIVEN** a social login flow that requires a signup confirmation
- **WHEN** the user is redirected to the signup page
- **THEN** the page is rendered using `templates/socialaccount/signup.html`
- **AND** it extends `base.html` and uses the brand theme.
