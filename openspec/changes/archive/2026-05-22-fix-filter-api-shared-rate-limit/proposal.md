# Fix: Filter API Shared Rate-Limit Outage

## Why

In production (`https://fastjob.es/`, deployed on Coolify behind a Traefik
reverse proxy) the sector/location filter on **both** the public landing page
and the authenticated client dashboard intermittently "stops working for all
users at once". A read-only source analysis traced this to a single root
cause with several aggravating factors.

**Root cause — one shared rate-limit bucket for the whole site.**
`apps/companies/views.py` protects the two endpoints that feed the filter
widget — `GET /api/companies/filter-options/` (`30/h`) and
`GET /api/companies/count/` (`60/h`) — with `@ratelimit(key="ip", block=True)`.
`django-ratelimit==4.1.0` resolves `key="ip"` via `core._get_ip()`, which —
when `RATELIMIT_IP_META_KEY` is unset (it is) — reads `request.META["REMOTE_ADDR"]`.
Behind Traefik, `REMOTE_ADDR` is the **proxy's container IP, identical for every
visitor**. All users therefore share one `30/h` bucket. `core._get_window()`
uses a fixed, value-jittered hourly window; because the jitter is derived from
that single shared IP, the window resets for everyone simultaneously. Result:
after ~30 page views in an hour the endpoint returns `429` to *everyone* until
the top of the next window — exactly the observed "intermittent, all-users,
self-healing" pattern.

**Aggravating factors confirmed in the code and the installed library:**

1. **Limits are far too low for public, per-pageview endpoints.** Every landing
   or dashboard load triggers one `filter-options` fetch; `30/h` site-wide is
   minutes of normal traffic.
2. **`django-ratelimit` fails *closed*.** `RATELIMIT_FAIL_OPEN` is unset
   (defaults `False`); `core.get_usage()` returns `should_limit=True` when the
   cache yields a `None` count (e.g. a Redis counter-key eviction). A cache
   blip can throttle every user with a clean `429` — a second, independent
   "all users at once" path.
3. **No client/CDN caching.** The `filter-options` response (a ~63 KB,
   slow-changing taxonomy) carries no `Cache-Control`, so every pageview —
   including crawlers and monitors — spends one unit of the budget.
4. **The front-end masks the failure.** `static/js/combobox.js` `fetchOptions()`
   calls `r.json()` without checking `r.ok`; a `text/plain` 429 body throws,
   the `.catch` swallows it, and the widget initialises with empty option
   lists and *no error shown*. The module-level `optionsPromise` singleton
   then freezes that empty state for the whole page session with no retry.

The same `REMOTE_ADDR` defect silently degrades the `@ratelimit(key="ip")`
limiters in `apps/mailing/views.py` too.

## What Changes

- **Resolve the real client IP.** Add a trust-bounded `X-Forwarded-For` parser
  and point `RATELIMIT_IP_META_KEY` at it, so every `@ratelimit(key="ip")` in
  the project keys on the actual visitor instead of the proxy. The number of
  trusted proxy hops is operator-configurable (`TRUSTED_PROXY_HOPS`, default
  `1` for Coolify/Traefik).
- **Raise and externalise the thresholds.** Move the `filter-options` and
  `count` rates into operator-configurable settings with realistic defaults.
- **Fail open for these endpoints.** Set `RATELIMIT_FAIL_OPEN = True` so a
  transient cache-backend disruption can no longer block all clients (rate
  limiting here is abuse-prevention, not a security control).
- **Make `filter-options` client-cacheable.** Emit a `Cache-Control` header so
  browsers and any edge cache stop spending budget on every pageview.
- **Harden `combobox.js`.** Check `r.ok`, stop memoising failed fetches, allow
  retry, and surface a visible, recoverable error instead of silent empty
  dropdowns.
- **Add observability.** Log a warning (Sentry breadcrumb) whenever a request
  is throttled, so the next incident is diagnosable without server logs.

No change to the public API contract, URLs, response schema, or data model.

## Impact

- **Affected specs:** `infrastructure` (ADDED ×1), `companies` (MODIFIED ×2,
  ADDED ×1), `landing` (MODIFIED ×1), `dashboard` (MODIFIED ×1).
- **Affected code:** new `apps/core/ratelimit.py`; `config/settings.py`
  (rate-limit section); `apps/companies/views.py` (rate values + cache
  headers); `apps/mailing/middleware.py` (throttle logging); `static/js/combobox.js`
  (resilient option loading). New tests under `apps/core/tests/` and
  `apps/companies/tests/`.
- **Behaviour change:** rate limits now apply per real visitor, not site-wide.
  This also repairs the IP keying of the `apps/mailing/views.py` limiters —
  intended and beneficial; no limiter ever legitimately relied on the
  collapsed proxy IP.
- **Operational:** new env vars `TRUSTED_PROXY_HOPS`, `RATELIMIT_FILTER_OPTIONS`,
  `RATELIMIT_FILTER_COUNT` (all have safe defaults; deployment works unchanged
  if they are not set). `TRUSTED_PROXY_HOPS` must be increased if a CDN is
  later placed in front of Traefik.
- **Risk:** trusting `X-Forwarded-For` incorrectly would reintroduce either the
  shared-bucket bug or a spoofing hole; mitigated by the trust-bounded parser
  and its tests — see `design.md`.
