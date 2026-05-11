# Proposal: Fix Email Sending Errors

## Objective
Fix two critical regressions preventing email sending in both production and local environments:
1. **Production**: The `process_mailing_queue` Celery task crashes with `psycopg2.ProgrammingError: can't adapt type 'Area'` because it is passing `Area` and `Location` model instances to `matching_companies_qs`, which expects strings.
2. **Local/Production**: The `No OAuth token found` error occurs because `django-allauth` is not configured to save OAuth tokens to the database, preventing background tasks from authenticating with Gmail/Microsoft.

## Scope
- Modify `matching_companies_qs` in `apps/companies/queries.py` to automatically normalize inputs (extracting the `.name` attribute if it receives model instances or QuerySets of model instances). This fixes the current bug and pre-emptively neutralizes an upcoming bug from the `allow-multiple-filters` feature.
- Update `config/settings.py` to add `SOCIALACCOUNT_STORE_TOKENS = True` so `django-allauth` persists the `SocialToken` records.

## Design
Instead of fixing the caller (`apps/mailing/tasks.py`), we harden the `matching_companies_qs` helper to accept either strings, model instances, or iterables of model instances. This makes the helper bulletproof and seamlessly supports the upcoming `allow-multiple-filters` feature which will start passing QuerySets of models instead of single models. The missing `SOCIALACCOUNT_STORE_TOKENS` is a configuration omission.