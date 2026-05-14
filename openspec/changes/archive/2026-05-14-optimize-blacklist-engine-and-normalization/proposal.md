# Change: Optimize Blacklist Engine and Normalization

## Why
1. **Scalability:** The current mailing engine loads all blacklisted emails into a Python `set` and passes them to an `__in` filter. This scales poorly and will eventually crash when the blacklist grows large (due to SQL query length limits).
2. **Data Consistency:** The `MailingLog.company_email_snapshot` field is not normalized to lowercase, which can lead to inconsistencies when looking up blacklist entries and a messy user interface.

## What Changes
- **Scalability Fix:** Refactor `process_mailing_queue` to use database-level subqueries for both blacklist exclusion and recently contacted companies.
- **Normalization Fix:** Add `LowercaseFieldsMixin` to the `MailingLog` model and ensure `company_email_snapshot` is always lowercased.
- **Robustness:** Ensure `company_email_snapshot` is always populated via a `clean()` validation and automatic population in `save()`.

## Impact
- Affected specs: `specs/mailing/spec.md`, `specs/companies/spec.md`
- Affected code: `apps/mailing/tasks.py`, `apps/mailing/models.py`, `apps/mailing/views.py`
