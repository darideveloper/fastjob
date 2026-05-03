## Context

The mailing engine sends one CV per active user per beat tick (1 minute), authenticated as that user against Gmail (`gmail.send`) or Microsoft Graph (`Mail.Send`). Tokens are stored in `allauth.socialaccount.models.SocialToken`:

- `SocialToken.token` = OAuth2 **access token** (1-hour TTL).
- `SocialToken.token_secret` = OAuth2 **refresh token** (long-lived).
- `SocialToken.expires_at` = access-token expiration timestamp.

Because the campaign is meant to run unattended for weeks/months, the refresh flow is the load-bearing component. The current implementation works on the happy path but breaks on edge cases that production *will* hit.

Provider-specific refresh-token lifetimes:

| Provider | Refresh token TTL | Rotation behavior |
|---|---|---|
| Google (Gmail) | Indefinite if project is in **Production**; **7 days** if in **Testing** | Stable — same value reused across refreshes (rare exceptions on scope change) |
| Microsoft (Graph) | **90-day rolling**: each refresh response returns a new `refresh_token`, and the 90-day clock resets *only if* the new value is persisted | Always rotates on confidential-client refresh |

## Goals / Non-Goals

**Goals**
- Make Microsoft accounts survive past 90 days of continuous use without re-link prompts.
- Stop pausing campaigns on transient upstream errors (5xx, network, 429).
- Make multi-linked-account behavior deterministic and explainable.
- Make the deploy-time configuration mistakes that silently break refresh (Google "Testing" mode, Azure single-tenant misconfig) loud at deploy time, not at day-7 / day-90.
- Give us enough log signal to notice rotation regressions early.

**Non-Goals**
- Replace django-allauth's `SocialToken` storage with a custom encrypted-at-rest model. Existing storage is acceptable; we just need to use it correctly.
- Support providers beyond Google + Microsoft.
- Build a full OAuth observability dashboard. Structured logs are sufficient — aggregation is delegated to Sentry / log search.
- Migrate already-issued Microsoft tokens. Whatever refresh tokens are currently in `token_secret` will be self-healed by the next successful refresh post-deploy.

## Decisions

### Decision: Persist `refresh_token` from the response when present

When the token endpoint returns a JSON body containing `refresh_token`, both `_refresh_google_token` and `_refresh_microsoft_token` MUST update `SocialToken.token_secret` and include `"token_secret"` in the `update_fields` argument to `.save()`.

- **Why:** Microsoft rotates on every refresh; Google rotates rarely. Writing unconditionally when present is correct for both.
- **Alternatives considered:**
  - *Microsoft-only rotation handling.* Rejected — symmetrical handling avoids a future Google rotation event silently breaking us, and costs nothing.
  - *Always overwrite even on absent field.* Rejected — would null out a working refresh token if the upstream response ever omits it (which Google often does).

### Decision: Two exception types — `TokenExpiredError` (terminal) and `TokenRefreshTransientError` (retry)

`engine.py` exports both. Mapping:

| HTTP / event | Exception | Reason |
|---|---|---|
| 400 with `error in {invalid_grant, invalid_client, unauthorized_client}` | `TokenExpiredError` | Refresh token is dead; user must re-link |
| 401, 403 | `TokenExpiredError` | Provider revoked access |
| 429 | `TokenRefreshTransientError` | Rate limit — back off, retry next tick |
| 5xx | `TokenRefreshTransientError` | Upstream outage |
| `requests.Timeout`, `requests.ConnectionError` | `TokenRefreshTransientError` | Network blip |
| Anything else | `TokenExpiredError` (conservative) | Unknown failure — treat as terminal so users are notified |

`process_mailing_queue` will:
- On `TokenRefreshTransientError`: log warning, mark the per-user `MailingLog` row as `FAILED` with the error message, **do not** flip `is_campaign_active`, **do not** queue `send_relink_notification`.
- On `TokenExpiredError`: existing behavior (pause campaign + notify).

- **Why:** A 5-minute Google API outage today bricks every active campaign and emails every user a "please re-link" message. That's a P0-grade self-inflicted incident waiting to happen.
- **Alternatives considered:**
  - *Use Celery task `autoretry_for` for transient errors.* Rejected for now — the task processes many users per tick; retrying the whole task on one user's transient failure would skip everyone else. Per-user no-op + next-beat retry is simpler and aligned with the slow-drip cadence.
  - *Inspect the JSON `error` field instead of the HTTP status.* Adopted in addition, not instead — both are used (status first for transport-level errors, JSON `error` for OAuth-protocol errors).

### Decision: Deterministic provider selection — most recently used wins

`_get_social_token(user)` MUST query `SocialAccount.objects.filter(user=user).order_by("-date_joined")` and select the first row, then select the most recently issued `SocialToken` for that account (`order_by("-id")` as a deterministic tiebreaker).

- **Why:** A user who later re-links a different provider almost certainly intends the new one to be used. `date_joined` on `SocialAccount` advances when allauth re-saves the account on re-link, so it's the right signal. Ordering by `-id` on `SocialToken` favors the most recently saved row, which is what refresh produces.
- **Alternatives considered:**
  - *Add a `User.preferred_oauth_provider` field.* Rejected as over-engineered for the current single-provider-per-user norm.
  - *Order by `last_login`.* Rejected — `SocialAccount.last_login` updates only on login, not on token refresh, so it doesn't track "most recent intent."

### Decision: Codify operational guardrails as runtime probes, not docs

Add to `config/health.py` (or a new `apps/mailing/health.py`) two checks consulted by `/healthz/`:

1. **Google project mode probe.** Read a new `GOOGLE_OAUTH_PROJECT_MODE` env var (default `"production"`). If set to `"testing"`, the healthcheck downgrades to a warning state and emits a structured log line on every probe. (We can't ask Google's API "is this app in Production?" — they don't expose it — so the env var is the contract.)
2. **Microsoft tenant probe.** Read `MICROSOFT_TENANT` env var (default `"common"`). If set to a tenant GUID and the Azure app is single-tenant, that's fine; if `"common"` is set but the app is single-tenant, refresh will 400. We can't probe Azure cheaply, so we document the contract and assert at deploy time via a `manage.py check_oauth_config` management command that hits the OpenID config endpoint for the configured tenant.

- **Why:** The whole point is to fail loudly at deploy time, not silently at day 90. Healthcheck integration means the existing readiness probe catches it.
- **Alternatives considered:**
  - *Just write docs.* Rejected — these are exactly the kind of subtle infra mistakes that get re-introduced on environment rebuilds.
  - *Probe Google for project status.* Rejected — Google does not expose project status via API.

### Decision: Structured logging for every refresh attempt

A single `logger.info` call at the end of each refresh helper, with a JSON-friendly payload via the `extra=` argument: `{"provider": "...", "user_pk": ..., "outcome": "...", "latency_ms": ..., "rotated": true|false}`. `outcome` is one of `hit_cache`, `refreshed`, `rotated`, `transient_error`, `terminal_error`.

- **Why:** Lets us answer "is rotation working?" with a log query instead of a database scan, and gives Sentry / log aggregation enough to alert on transient-error spikes.
- **Alternatives considered:**
  - *Add a `RefreshAttempt` table.* Rejected — high write volume, no aggregation tooling needed beyond logs.
  - *Use Django signals.* Rejected — direct logging is simpler and the call sites are few.

## Risks / Trade-offs

- **Risk:** Persisting a *new* refresh token mid-flight introduces a race if two workers refresh the same user concurrently — the second writer's value clobbers the first. **Mitigation:** Wrap the refresh + save in `select_for_update()` inside a transaction (atomic), gated on the existing 60-second skew window so cache hits short-circuit before the lock.
- **Risk:** Misclassifying a real `invalid_grant` as transient would mean a user whose token was actually revoked never gets the relink email. **Mitigation:** The mapping table is conservative — anything unrecognized falls through to `TokenExpiredError`. Add a regression test for each enumerated error code.
- **Risk:** The Google project-mode env var is operator-set, so an operator who forgets to set it (or sets `production` while actually in `Testing`) defeats the guard. **Mitigation:** Make the deployment runbook list this var as required; the management command `check_oauth_config` will at least verify the secret/client_id pair resolves.
- **Trade-off:** Two exception types adds API surface for any future internal caller. Acceptable: the engine is a small private module.

## Migration Plan

1. **Deploy code.** No database migration required.
2. **Roll out.** First Microsoft refresh after deploy will read the existing (possibly old) refresh token, exchange it for a new one, and persist the rotated value — self-healing for any user who refreshes within their remaining 90-day window.
3. **Verify.** Within 24h of deploy, query logs for `outcome=rotated provider=microsoft` — should be non-zero. Query for `outcome=terminal_error` and confirm the count matches expectations (existing pre-deploy baseline ± noise).
4. **Rollback.** Pure code change; revert the commit. Already-rotated Microsoft tokens remain valid (we wrote them; reverting the writer doesn't invalidate them).

## Open Questions

- Should the structured log payloads also be emitted as Sentry breadcrumbs for failed sends? Probably yes, but treating it as a follow-up keeps this change scoped.
- Do we want a per-user "OAuth health" indicator in the dashboard so users can see their own token status before the campaign pauses? Out of scope here; track separately if asked.
