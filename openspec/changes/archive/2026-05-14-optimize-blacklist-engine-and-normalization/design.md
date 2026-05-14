## Context
The system currently handles blacklisting by loading all blacklisted emails into memory at the start of each mailing engine "tick". As the user base and blacklist grow, this will hit SQL parameter limits (e.g., 65,535 parameters in some databases) or cause performance degradation due to massive query strings.

## Goals
- Move blacklist exclusion to a database-level subquery.
- Ensure all email snapshots in `MailingLog` are lowercased for consistency.

## Decisions
- **Decision:** Use `Company.objects.exclude(email__in=Blacklist.objects.values("email"))` in the mailing engine.
  - **Rationale:** This creates a `NOT IN (SELECT email FROM blacklist)` subquery, which is handled efficiently by the database and does not involve passing large lists of strings from Python to SQL.
- **Decision:** Apply `LowercaseFieldsMixin` to `MailingLog`.
  - **Rationale:** This ensures that any value written to `company_email_snapshot` is automatically normalized, preventing case-mismatch issues.

## Risks / Trade-offs
- **Risk:** A database-level subquery might be slower than an in-memory set if the blacklist is small and the `Company` table is huge without proper indexing.
  - **Mitigation:** Ensure `Blacklist.email` and `Company.email` are indexed (they are already unique, so they are indexed).
