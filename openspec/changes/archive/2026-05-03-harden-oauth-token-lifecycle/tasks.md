# Tasks

## 1. Engine: refresh-token rotation persistence
- [x] 1.1 Update `_refresh_google_token` in `apps/mailing/engine.py` to persist `data["refresh_token"]` into `token.token_secret` when the field is present in the response, and include `"token_secret"` in `update_fields`.
- [x] 1.2 Apply the symmetric change to `_refresh_microsoft_token`.
- [x] 1.3 Wrap the refresh-and-save block in `transaction.atomic()` + `SocialToken.objects.select_for_update().get(pk=token.pk)` to serialize concurrent refreshes for the same user. Keep the pre-lock 60-second skew check so cache hits short-circuit before acquiring the lock.

## 2. Engine: transient-vs-terminal error classification
- [x] 2.1 Add `TokenRefreshTransientError(Exception)` alongside the existing `TokenExpiredError` in `apps/mailing/engine.py`.
- [x] 2.2 Introduce a private `_classify_refresh_failure(resp_or_exc) -> Exception` helper implementing the mapping table from `design.md` (HTTP 5xx / 429 / network errors → transient; 401/403 / `invalid_grant`-class 400 / unknown → terminal).
- [x] 2.3 Replace the current `if resp.status_code != 200: raise TokenExpiredError(...)` blocks in both refresh helpers with `raise _classify_refresh_failure(resp)`.
- [x] 2.4 Wrap `requests.post(...)` calls in try/except for `requests.Timeout` / `requests.ConnectionError`, routing through `_classify_refresh_failure`.

## 3. Engine: deterministic provider/token selection
- [x] 3.1 In `_get_social_token`, replace `socialaccount_set.select_related().first()` with an ordered query: `user.socialaccount_set.order_by("-date_joined").first()`.
- [x] 3.2 Replace `social.socialtoken_set.first()` with `social.socialtoken_set.order_by("-id").first()`.
- [x] 3.3 Add a docstring noting the selection rule so it does not silently get reverted.

## 4. Tasks: handle the new exception in the worker
- [x] 4.1 In `apps/mailing/tasks.py::process_mailing_queue`, add an `except TokenRefreshTransientError as exc:` branch *before* the `except Exception` catch-all. Log a warning, mark the `MailingLog` row `FAILED` with the error message, but do NOT flip `is_campaign_active` and do NOT enqueue `send_relink_notification`.
- [x] 4.2 Confirm the existing `TokenExpiredError` branch retains its current behavior (campaign pause + relink email).

## 5. Operational guardrails
- [x] 5.1 Add `GOOGLE_OAUTH_PROJECT_MODE` (default `"production"`) read via `python-decouple` in `config/settings.py`.
- [x] 5.2 Add `MICROSOFT_TENANT` (default `"common"`) read via `python-decouple` in `config/settings.py`. Update `_refresh_microsoft_token` to use `f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT}/oauth2/v2.0/token"`.
- [x] 5.3 In `config/health.py`, add a `oauth_config_check()` probe that returns `WARNING` when `GOOGLE_OAUTH_PROJECT_MODE == "testing"` and emits a structured log line. Wire it into `/healthz/` so it surfaces alongside existing checks.
- [x] 5.4 Add a `manage.py check_oauth_config` management command under `apps/mailing/management/commands/check_oauth_config.py` that GETs the OpenID discovery doc for the configured `MICROSOFT_TENANT` and the Google token endpoint, returning non-zero exit code if either is unreachable or returns a config mismatch.
- [x] 5.5 Document both env vars in `README.md` under the deployment section.

## 6. Structured logging
- [x] 6.1 In each refresh helper, capture `t0 = time.monotonic()` at the top, compute `latency_ms` after the response, and emit one `logger.info("oauth_refresh", extra={...})` call with `provider`, `user_pk`, `outcome` (`hit_cache` | `refreshed` | `rotated` | `transient_error` | `terminal_error`), `latency_ms`, `rotated` boolean.
- [x] 6.2 Confirm the logging format does not include the access or refresh token values themselves (regression guard against secret leakage).

## 7. Tests
- [x] 7.1 Create `apps/mailing/tests/test_engine.py` if missing. *(Already existed; appended new cases.)*
- [x] 7.2 Add `test_microsoft_refresh_persists_rotated_refresh_token`: mock the token endpoint to return a new `refresh_token`; assert `SocialToken.token_secret` is updated and the in-memory token reflects it.
- [x] 7.3 Add `test_google_refresh_persists_refresh_token_when_present`.
- [x] 7.4 Add `test_refresh_skips_when_unexpired_within_skew_window`: precondition `expires_at = now + 5 min`; assert no HTTP call is made.
- [x] 7.5 Add `test_5xx_raises_transient_error` (parameterized for both providers).
- [x] 7.6 Add `test_invalid_grant_raises_token_expired` (parameterized for both providers).
- [x] 7.7 Add `test_429_raises_transient_error`.
- [x] 7.8 Add `test_network_timeout_raises_transient_error`.
- [x] 7.9 In `apps/mailing/tests/test_tasks.py`, add `test_transient_refresh_error_does_not_pause_campaign`: assert `is_campaign_active` remains `True` and `send_relink_notification` is not called.
- [x] 7.10 Add `test_terminal_refresh_error_pauses_campaign_and_emails_user`: assert existing behavior is preserved.
- [x] 7.11 Add `test_user_with_two_linked_providers_uses_most_recent`: create two `SocialAccount` rows with different `date_joined`; assert the newer one is chosen.
- [x] 7.12 Add a healthcheck test asserting `/healthz/` returns a warning indicator when `GOOGLE_OAUTH_PROJECT_MODE=testing`.

### 7.bis Extra tests added beyond the proposal (per the user's "add any required test")
- [x] 7.bis.1 `test_google_refresh_preserves_existing_refresh_token_when_absent` — guards against the symmetric mistake of nulling out `token_secret` when the response omits it (Google's normal case).
- [x] 7.bis.2 `test_connection_error_raises_transient_error` — pairs with the timeout test for the second `requests` exception class we route as transient.
- [x] 7.bis.3 `test_401_raises_token_expired` — covers the 401 branch of the classifier explicitly.
- [x] 7.bis.4 Six direct unit tests on `_classify_refresh_failure` (5xx, 429, known OAuth errors, unknown 4xx, Timeout, ConnectionError) — independent of provider plumbing so a future provider can reuse the mapping.
- [x] 7.bis.5 `test_user_with_multiple_tokens_per_provider_uses_newest` — covers the `order_by("-id")` half of the selection rule using two `SocialApp` rows (the realistic credentials-rotation scenario, since the DB enforces UNIQUE(app_id, account_id)).
- [x] 7.bis.6 Three structured-logging tests — `outcome=rotated` happy path with explicit token-leak assertion across every `extra` field, `outcome=hit_cache` zero-latency, and `outcome=terminal_error` on `invalid_grant`.
- [x] 7.bis.7 `test_concurrent_refresh_does_not_double_call_provider` — verifies the cache fast-path keeps a back-to-back second call from re-hitting the provider after the first refresh mutated the in-memory token.
- [x] 7.bis.8 `test_healthz_no_warnings_in_production_mode` — negative-case companion to 7.12.

### 7.ter Gap-fill round (caught during post-implementation audit)
- [x] 7.ter.1 `test_locked_recheck_short_circuits_when_other_worker_already_refreshed` — true coverage for the spec scenario "Concurrent refreshes for the same user are serialized". Simulates worker A persisting a fresh token while worker B's in-memory copy is still stale; B must fall through the cheap check, acquire the row lock, re-read, and short-circuit without a duplicate POST.
- [x] 7.ter.2 `test_refresh_logs_outcome_transient_error_with_no_token_leak` — the spec scenario "Refresh failure logs outcome and never logs the token" enumerates BOTH `transient_error` and `terminal_error`; only the latter was covered before.
- [x] 7.ter.3 No-leak assertion added to `test_refresh_logs_outcome_terminal_error_on_invalid_grant` — same spec scenario explicitly forbids token strings in the failure log payload.
- [x] 7.ter.4 Log-emission assertion added to `test_healthz_warns_when_google_oauth_in_testing_mode` — the spec scenario says "AND a structured log line is emitted with the warning"; previously only the response body was asserted.
- [x] 7.ter.5 New `apps/mailing/tests/test_check_oauth_config_command.py` with 3 cases: bad Microsoft tenant exits non-zero, both endpoints reachable succeeds, network error to Microsoft exits non-zero. Covers the spec scenario "check_oauth_config command fails when Microsoft tenant is misconfigured" — the management command was implemented but had no test in the original tasks list.

## 8. Docs and runbook
- [x] 8.1 Update `README.md` documenting the two env vars, the `Production` vs `Testing` Google distinction, the single-tenant Microsoft caveat, and how to verify rotation in logs.
- [x] 8.2 Note in `openspec/project.md` "Important Constraints" that long-running OAuth correctness is governed by the new mailing-spec requirements.

## 9. Validation
- [x] 9.1 Ran `pytest apps/mailing/tests -v` — **90 passed** (was 85 before the gap-fill round). Full project suite: **180 passed, 0 failed**.
- [x] 9.2 Ran `openspec validate harden-oauth-token-lifecycle --strict` — `Change 'harden-oauth-token-lifecycle' is valid`.
- [x] 9.3 *(Manual / out-of-scope for this code change.)* Exercise the flow in a staging environment with one Google and one Microsoft account; verify log lines `outcome=rotated provider=microsoft` appear after the first post-deploy refresh.
