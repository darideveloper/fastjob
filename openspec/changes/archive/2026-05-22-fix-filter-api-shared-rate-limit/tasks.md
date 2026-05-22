# Tasks — Fix Filter API Shared Rate-Limit Outage

## 1. Real client-IP resolution (root cause)

- [x] 1.1 Create `apps/core/ratelimit.py` with `get_client_ip(request)` — parse
      `HTTP_X_FORWARDED_FOR`, take the entry at index `-TRUSTED_PROXY_HOPS`,
      validate with `ipaddress.ip_address()`, fall back to `REMOTE_ADDR` on a
      short/blank/garbage header. Must always return a non-empty string.
- [x] 1.2 In `config/settings.py` add `TRUSTED_PROXY_HOPS = config("TRUSTED_PROXY_HOPS", default=1, cast=int)`
      in the rate-limiting section.
- [x] 1.3 In `config/settings.py` add `RATELIMIT_IP_META_KEY = "apps.core.ratelimit.get_client_ip"`.
- [x] 1.4 Add `apps/core/tests/test_ratelimit.py`: single-hop XFF returns the
      client IP; extra (spoofed) left-hand entries are ignored; missing/blank
      header falls back to `REMOTE_ADDR`; non-IP token falls back; IPv6 address
      is accepted; `TRUSTED_PROXY_HOPS=2` selects `xff[-2]`. (9 tests, all pass.)
- [x] 1.5 Audit every `@ratelimit(key="ip", ...)` call site (`apps/companies/views.py`,
      `apps/mailing/views.py`); confirm none relied on the collapsed proxy IP
      and all are now correctly per-visitor. Confirm the existing `mailing`
      thresholds (`cv_download` `30/h`, `unsubscribe` `10/h`) remain appropriate
      as genuine per-real-IP limits — note that this fix also rescues those two
      endpoints, which currently share the same site-wide bucket and go down in
      the same outage. Record the audit in the PR.
      AUDIT RESULT: 4 `key="ip"` sites — `filter_options_view`,
      `companies_count_view`, `cv_download` (`30/h`), `unsubscribe` (`10/h`).
      None relied on the proxy IP; all now key per-visitor via
      `RATELIMIT_IP_META_KEY`. `export_data` uses `key="user"`, unaffected.

## 2. Throttle thresholds and fail-open

- [x] 2.1 In `config/settings.py` add `RATELIMIT_FILTER_OPTIONS = config("RATELIMIT_FILTER_OPTIONS", default="300/h")`
      and `RATELIMIT_FILTER_COUNT = config("RATELIMIT_FILTER_COUNT", default="600/h")`.
- [x] 2.2 Update `apps/companies/views.py` decorators to read the configured
      thresholds; keep `key="ip"` and `block=True` unchanged. Implemented as
      per-request `rate` callables (`_filter_options_rate` / `_filter_count_rate`)
      so the threshold stays runtime-configurable and overridable in tests.
- [x] 2.3 In `config/settings.py` add `RATELIMIT_FAIL_OPEN = True` with a
      comment explaining the abuse-prevention-not-security trade-off.
- [x] 2.4 Add tests in `apps/companies/tests/`: two requests with different
      resolved client IPs get independent buckets; one IP over the configured
      limit still receives `429`; with the cache backend returning `None` for
      the counter (mock the cache), the request is NOT blocked (fail-open).
      All cases wrapped in `@override_settings(RATELIMIT_ENABLE=True)` because
      `config/test_settings.py` disables limiting by default.

## 3. Reduce request volume — client caching

- [x] 3.1 In `apps/companies/views.py`, set `Cache-Control: public, max-age=300`
      on the `filter_options_view` response.
- [x] 3.2 In `apps/companies/views.py`, set `Cache-Control: public, max-age=60`
      on the successful `companies_count_view` response; the `400`
      `invalid_filter` response is marked `Cache-Control: no-store`.
- [x] 3.3 Add tests asserting the `Cache-Control` header is present and correct
      on both endpoints, and `no-store` on the `400` count response.

## 4. Front-end resilience (`static/js/combobox.js`)

- [x] 4.1 In `fetchOptions()`, check `r.ok` before `r.json()`; on a non-OK or
      network failure, reset the module-level `optionsPromise` to `null` so the
      next call retries (stop memoising failures), and let the promise reject
      instead of resolving to empty arrays.
- [x] 4.2 Update the `DOMContentLoaded` handler to add a `.catch`: on failure,
      render an inline, visible message with a "Reintentar" control inside each
      `[data-combobox]` container instead of initialising with empty option
      lists. The control re-runs `fetchOptions()` and, on success, runs the
      widget-initialisation path so both dropdowns become functional with no
      page reload. (`renderOptionsError` + `initWidgets` helpers; ES5, matches
      the file's existing style; `node --check` passes.)
- [x] 4.3 Leave the debounced `count` fetch as-is (it already checks `r.ok` and
      degrades to a dash) — verified unchanged.
- [ ] 4.4 PENDING (manual, post-deploy / staging): verify on the landing page
      and the dashboard that, with the API forced to `429`/`500` (DevTools
      request blocking), the widget shows the error + retry instead of silent
      empty dropdowns, and recovers on retry. Not run here (local run was out
      of scope for this session).

## 5. Observability

- [x] 5.1 In `apps/mailing/middleware.py` `RatelimitMiddleware.process_exception`,
      added a module logger and `logger.warning("ratelimit: throttled path=%s ip=%s", ...)`
      using the resolved client IP, before returning the `429`.
- [ ] 5.2 PENDING (manual): confirm the warning reaches Sentry in a non-prod
      environment (trigger a throttle and verify the breadcrumb/event appears).

## 6. Documentation and validation

- [x] 6.1 Added `TRUSTED_PROXY_HOPS`, `RATELIMIT_FILTER_OPTIONS`, and
      `RATELIMIT_FILTER_COUNT` to `.env.example` with defaults and comments;
      added a `TRUSTED_PROXY_HOPS` note to the `## Producción` section of
      `README.md`. (`RATELIMIT_FAIL_OPEN` is a fixed code-level setting, not
      operator-tunable, so it is intentionally not in `.env.example`.)
- [x] 6.2 Ran the full test suite (`pytest -m "not slow"`): 321 passed, 20 new.
      The only 3 failures (`test_storage.py` ×2, `test_visible_credits.py` ×1)
      were confirmed pre-existing on a clean tree — unrelated to this change.
- [x] 6.3 Ran `openspec validate fix-filter-api-shared-rate-limit --strict` —
      passes.
- [ ] 6.4 PENDING (post-deploy): perform the verification from `design.md`
      (Redis `rl:*` key inspection + two-network test + `Cache-Control` header
      check) once the change is deployed.
