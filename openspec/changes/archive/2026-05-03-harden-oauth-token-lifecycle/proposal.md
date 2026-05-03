# Change: Harden OAuth token lifecycle for long-running background sends

## Why

The slow-drip mailing engine (`apps/mailing/engine.py`) refreshes the user's OAuth access token before every send, but it has gaps that break the "run in background for months" promise the product depends on:

1. **Critical — Microsoft refresh tokens are silently dropped on rotation.** `_refresh_microsoft_token` reads `access_token` and `expires_in` from the response and saves them to `SocialToken.token` / `SocialToken.expires_at`, but ignores the new `refresh_token` value Microsoft returns on every refresh call. Microsoft's "rolling 90-day" refresh token only stays alive if the rotated value is persisted; today, every Microsoft user's campaign will hard-fail on day 90 regardless of activity. The same defensive write would also future-proof Google, which can return a new refresh token on rare occasions (scope changes, security events).
2. **Transient API errors are misclassified as terminal.** Both refresh helpers raise `TokenExpiredError` on *any* non-200 response, which `process_mailing_queue` interprets as "user must re-link" — pausing the campaign (`is_campaign_active = False`) and emailing them. A 503 from Google, a connection timeout, or a 429 rate-limit will incorrectly suspend an active paying user.
3. **Multi-provider account selection is non-deterministic.** `_get_social_token` calls `socialaccount_set.first()` and `socialtoken_set.first()` with no ordering. A user who has linked both Google and Microsoft (e.g., signed up with one and later linked the other) gets a randomly chosen provider per request.
4. **Operational guardrails are unspecified.** Google's refresh token expires after 7 days if the OAuth consent screen is in *Testing* mode; Microsoft refresh requires the Azure app to be configured as multi-tenant given the `/common/` endpoint usage. Neither is asserted anywhere in the spec, so a future deploy can silently regress.
5. **Refresh observability is thin.** Today we only log `error=...` on failure. We can't answer "how many refreshes succeeded today?", "which provider is failing more?", or "did this user's last refresh include a rotated refresh token?" — needed both to debug regressions and to detect rotation breakage early.

## What Changes

- **Persist rotated refresh tokens.** Both Google and Microsoft refresh paths MUST write `SocialToken.token_secret` whenever the response includes a `refresh_token`, and include `token_secret` in the `update_fields` list for that case.
- **Classify refresh failures into transient vs terminal.** Introduce a `TokenRefreshTransientError` (separate from `TokenExpiredError`) covering 5xx responses, network/timeout exceptions, and HTTP 429. `process_mailing_queue` MUST treat transient errors as a no-op for that user-tick (no campaign pause, no relink email) and let the next beat retry. Only `TokenExpiredError` (4xx with `invalid_grant`-class errors) pauses the campaign. **BREAKING for callers of `_refresh_google_token` / `_refresh_microsoft_token`** — they may now raise a new exception type.
- **Make multi-provider selection deterministic.** `_get_social_token` MUST select the most recently used social account (`SocialAccount` ordered by `date_joined`/`last_login` descending) when more than one provider is linked, and MUST select the most recently issued token for that social account.
- **Codify operational guardrails.** Add a deploy-time healthcheck (or admin command) that asserts: the Google OAuth consent screen is not in `Testing` status (probed via the discovery doc / a config flag in `settings.py`) and that the Microsoft client is multi-tenant. Failures surface in the existing `/healthz/` endpoint.
- **Add structured logging for every refresh outcome.** Each refresh attempt logs `provider`, `user_pk`, `outcome` (`hit_cache` / `refreshed` / `rotated` / `transient_error` / `terminal_error`), and `latency_ms`. Surface counters via the existing logger so they can be aggregated in Sentry/observability.

## Impact

- **Affected specs:** `mailing` (one delta, additive — orthogonal to existing filter-semantics requirements).
- **Affected code:**
  - `apps/mailing/engine.py` — `_refresh_google_token`, `_refresh_microsoft_token`, `_get_social_token`, plus a new `TokenRefreshTransientError` exception.
  - `apps/mailing/tasks.py` — `process_mailing_queue` exception handling chain.
  - `config/health.py` — add OAuth-config guardrail probes.
  - `config/settings.py` — optional `GOOGLE_OAUTH_PROJECT_MODE` config flag (`production` / `testing`) consulted by the healthcheck.
  - Tests: `apps/mailing/tests/test_tasks.py` (new transient-vs-terminal cases) and a new `apps/mailing/tests/test_engine.py` if it does not yet exist (token-rotation persistence cases, deterministic selection cases).
- **Operational impact:** none for end users on the happy path; Microsoft users currently approaching the 90-day cliff will have their refresh tokens healed on the next successful send after deploy. No data migration required (rotated tokens overwrite the existing `token_secret` in place).
- **Out of scope:** moving away from django-allauth's `SocialToken` storage, encrypting the column at rest beyond what allauth provides, supporting additional providers.
