# accounts Specification Delta (migrate-social-creds-to-db)

## MODIFIED Requirements

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
