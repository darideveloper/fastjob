# Proposal: Migrate Social Credentials to Database

## Summary
Currently, social authentication credentials (Google and Microsoft Client IDs and Secrets) are stored in the `.env` file and loaded into `settings.SOCIALACCOUNT_PROVIDERS`. This proposal migrates these credentials to the `SocialApp` database model. This change allows for credential management through the Django Admin interface and aligns with projects where credentials might need rotation without code/deployment changes.

## Motivation
- **Flexibility:** Allows updating OAuth credentials via the Django Admin without requiring a server restart or deployment.
- **Consistency:** Uses the standard `django-allauth` model for credential storage.
- **Decoupling:** Removes OAuth secrets from the environment configuration, treating them as dynamic data.

## Scope
- Update `config/settings.py` to remove hardcoded `APP` credentials.
- Update `apps/mailing/engine.py` to fetch credentials from the `SocialApp` model.
- Provide a migration script to safely transfer existing `.env` values to the database.
- Update documentation and `docker-compose.yml` to reflect the removal of OAuth secrets from the environment.
- Verify that both login and background email sending (mailing engine) continue to work seamlessly.
