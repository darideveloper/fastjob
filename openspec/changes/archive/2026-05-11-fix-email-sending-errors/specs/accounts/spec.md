## ADDED Requirements

### Requirement: Persist OAuth Tokens for Background Mailing
The system MUST explicitly configure `django-allauth` to store OAuth tokens in the database (`SOCIALACCOUNT_STORE_TOKENS = True`). This ensures the background mailing engine can retrieve the `SocialToken` required to send emails on the user's behalf via the Gmail/Microsoft Graph APIs.

#### Scenario: Background engine has access to saved tokens
- **GIVEN** `SOCIALACCOUNT_STORE_TOKENS` is `True`
- **WHEN** a user completes the OAuth login flow
- **THEN** their `SocialToken` is saved to the database
- **AND** the mailing engine's `_get_social_token(user)` successfully retrieves it without throwing a `TokenExpiredError: No OAuth token found.`