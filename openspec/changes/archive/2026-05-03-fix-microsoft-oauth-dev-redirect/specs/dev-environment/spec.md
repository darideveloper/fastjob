# dev-environment Specification Delta

## MODIFIED Requirements

### Requirement: Development Environment Domain Support
The application MUST support incoming requests from the development localtunnel subdomain (`fastjob.loca.lt`) and correctly handle HTTPS termination.

#### Scenario: A developer initiates Microsoft OAuth login via localtunnel.
- **Given** the application is running via `localtunnel` at `https://fastjob.loca.lt`
- **AND** `TRUST_PROXY_SSL_HEADER` is set to `True`
- **When** the developer clicks "Login with Microsoft"
- **Then** the generated `redirect_uri` sent to Microsoft MUST use the `https` scheme.
- **AND** the URI MUST be `https://fastjob.loca.lt/accounts/microsoft/login/callback/`.
