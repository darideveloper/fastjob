# mailing Specification Delta (migrate-social-creds-to-db)

## MODIFIED Requirements

### Requirement: Mailing Engine Token Refresh
The mailing engine MUST use credentials from the `SocialApp` database model for all OAuth2 token refresh operations. This ensures that credential updates in the database take immediate effect for background tasks.

#### Scenario: Token refresh retrieves credentials from DB
- **GIVEN** a valid `SocialApp` record exists for the provider (e.g., 'google') with correct `client_id` and `secret`.
- **AND** a user's `SocialToken` is expired.
- **WHEN** the mailing engine attempts to refresh the token.
- **THEN** it MUST query the `SocialApp` table for the provider's credentials.
- **AND** use those credentials in the POST request to the provider's token endpoint.
- **AND** the refresh succeeds if the credentials match the provider's records.

#### Scenario: Missing SocialApp record raises error
- **GIVEN** no `SocialApp` record exists for a linked provider.
- **WHEN** the mailing engine attempts a token refresh.
- **THEN** it MUST raise a `TokenExpiredError` (or similar) indicating that the OAuth configuration is missing.
- **AND** the error message MUST specify the missing provider.
