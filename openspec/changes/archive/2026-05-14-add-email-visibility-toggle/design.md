## Context
The client wants to dynamically control whether sent emails are visible in users' sent folders globally from a system dashboard. Currently, Microsoft emails are hidden (hardcoded) and Google emails are shown (default behavior of `users.messages.send`).

## Goals / Non-Goals
- Goals: Allow a system administrator to toggle sent email visibility globally for all users across the platform. Apply this setting to both Microsoft and Google OAuth providers.
- Non-Goals: Providing per-user toggles for this feature.

## Decisions
- Decision: Use a Singleton `SystemConfig` model in `apps/core/models.py` accessible via Django Admin.
- Alternatives considered: Using `django-constance`. We decided against it to avoid introducing a new dependency for a single toggle, maintaining the "boring, proven patterns" philosophy.

- Decision: For Gmail, we will immediately delete the message after sending it if the global toggle is off.
- Alternatives considered: Using a custom SMTP relay or filters. This would break the core requirement of sending from the user's OAuth account to maintain their specific sender reputation.

## Risks / Trade-offs
- Risk: Changing the Gmail scope from `gmail.send` to `gmail.modify` upgrades the app from requesting a "Sensitive" scope to a "Restricted" scope.
- Mitigation: The client must be informed that this requires a CASA Tier 2/3 security audit by Google, costing significant time and money. Existing users will also see a re-consent screen. If the client decides this is not worth it, the Gmail portion of this feature must be dropped or modified.

## Migration Plan
1. Deploy code with `SystemConfig` model.
2. Update Google Cloud Console with new `gmail.modify` scope and submit for verification.
3. Once verified, users will be prompted to re-link their Google accounts to accept the new permissions.

## Open Questions
- Is the client prepared for the Google CASA audit process and costs associated with the `gmail.modify` scope?
