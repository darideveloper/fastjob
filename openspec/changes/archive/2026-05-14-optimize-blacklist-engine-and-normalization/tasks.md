## 1. Normalization & Robustness (MailingLog)
- [x] 1.1 Update `apps/mailing/models.py` to add `LowercaseFieldsMixin` to `MailingLog` and define `lowercase_fields = ["company_email_snapshot"]`.
- [x] 1.2 Add `clean()` validation to `MailingLog` to ensure `company_email_snapshot` is not empty.
- [x] 1.3 Create and run migration to normalize existing `company_email_snapshot` values in the database.

## 2. Scalability Fix (Mailing Engine)
- [x] 2.1 Update `apps/mailing/tasks.py` to replace in-memory `blacklisted_emails` with a subquery.
- [x] 2.2 Update `apps/mailing/tasks.py` to replace initial `recently_contacted_ids` with a subquery, while maintaining a small in-memory set for "in-tick" exclusions.

## 3. Verification
- [x] 3.1 Add unit test to verify `MailingLog` normalizes `company_email_snapshot` on save.
- [x] 3.2 Add integration test to verify the mailing engine correctly excludes blacklisted companies using the subquery approach.
- [x] 3.3 Verify `MailingLog.clean()` raises error on empty snapshot.
