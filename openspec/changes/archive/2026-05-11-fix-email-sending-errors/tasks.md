# Tasks

- [x] 1. Harden `matching_companies_qs` to accept models and iterables.
  - In `apps/companies/queries.py`, update `matching_companies_qs` to inspect the `area` and `location` arguments.
  - If an argument is a model instance (e.g., has a `.name` attribute), extract the `.name`.
  - If it is an iterable (like a QuerySet or list) of model instances, extract a list of their `.name`s.
  - Apply the filter using `__iexact` for a single string, or `__in` for a list of strings.
  - This fixes the current `psycopg2.ProgrammingError` and provides seamless support for the upcoming `allow-multiple-filters` implementation.
- [x] 2. Fix missing OAuth tokens for background mailing.
  - In `config/settings.py`, add `SOCIALACCOUNT_STORE_TOKENS = True` alongside other `SOCIALACCOUNT_*` settings.