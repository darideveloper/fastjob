# Design — Fix Filter API Shared Rate-Limit Outage

## Context

`django-ratelimit==4.1.0`, `Django==4.2.16`, deployed on Coolify (Traefik
reverse proxy). Verified library behaviour from the installed source:

- `core._get_ip(request)` — if `settings.RATELIMIT_IP_META_KEY` is unset, uses
  `request.META["REMOTE_ADDR"]`. If set, it accepts a **callable**, a **dotted
  import path** (string containing `.`), or a **plain `META` key** name.
- `core._get_window(value, period)` — fixed window:
  `w = ts - (ts % period) + (zlib.crc32(value) % period)`. Jitter depends on
  the key `value`; a shared value ⇒ a synchronised reset for all callers.
- `core.get_usage()` — on a `None`/`False` count from the cache, returns
  `should_limit=True` **unless** `settings.RATELIMIT_FAIL_OPEN` is truthy
  (it defaults to `False`).

Pre-existing project configuration that this design depends on:

- `config/settings.py` already sets `CACHES["default"]["OPTIONS"]["IGNORE_EXCEPTIONS"] = True`
  on the Redis cache. `django-redis` therefore converts a Redis outage into a
  `None`/miss return instead of raising. This has two consequences the rest of
  this design relies on: (a) a Redis outage makes `core.get_usage()` see a
  `None` count and hit the fail-closed branch — so the current failure mode is
  a **clean `429` for everyone, not a `500`**; and (b) the data-cache reads in
  `apps/companies/queries.py` (`get_filter_options`, `get_company_count`)
  already degrade to a direct DB query on Redis-down rather than erroring. Both
  are why `RATELIMIT_FAIL_OPEN = True` is a *complete* resilience fix here with
  no additional cache-hardening work required (see Decision 4).

## Goals / Non-Goals

**Goals:** rate limits keyed per real visitor; a cache blip cannot throttle
everyone; far fewer requests reach the throttle; failures are visible and
recoverable in the UI; the next incident is diagnosable.

**Non-Goals:** no change to the API contract, URLs, response schema, taxonomy,
or data model. No new runtime dependency. No rewrite of Django's global
`REMOTE_ADDR` (see Decision 3). No front-end test framework is introduced
(none exists; `combobox.js` changes are manually verified).

## Decision 1 — Trust-bounded `X-Forwarded-For` parser

New module `apps/core/ratelimit.py`:

```python
def get_client_ip(request) -> str:
    """Resolve the real client IP for rate-limiting, bounded by the number
    of trusted reverse-proxy hops. Never returns an empty string."""
```

Algorithm:

1. Read `TRUSTED_PROXY_HOPS` (settings, default `1`).
2. Read `request.META.get("HTTP_X_FORWARDED_FOR")`. If absent/blank, return
   `request.META.get("REMOTE_ADDR", "")`.
3. Split on `,`, strip whitespace, drop empties → `xff` list.
4. Each proxy appends *its own immediate peer*. The entry the outermost
   trusted proxy observed is `xff[-TRUSTED_PROXY_HOPS]`. If
   `len(xff) >= TRUSTED_PROXY_HOPS`, take that entry; otherwise the header is
   malformed/short → fall back to `REMOTE_ADDR`.
5. Validate the chosen value with `ipaddress.ip_address()`; on failure fall
   back to `REMOTE_ADDR`. This rejects garbage and the spoof where a client
   pre-seeds a non-IP token.

**Why trust-bounded counting from the right.** `X-Forwarded-For` is *appended*
by every hop, so the leftmost entries are attacker-controlled. Only entries
contributed by infrastructure *we* operate are trustworthy, and those are the
rightmost `TRUSTED_PROXY_HOPS`. Coolify/Traefik = exactly one hop ⇒ default
`1`, and `xff[-1]` is the genuine client. If a CDN is later added in front,
the operator bumps `TRUSTED_PROXY_HOPS` to `2`.

**Anti-pattern explicitly rejected:** `RATELIMIT_IP_META_KEY = "HTTP_X_FORWARDED_FOR"`.
That hits django-ratelimit's plain-`META`-key branch and uses the **raw,
unparsed, client-spoofable** header as the bucket key — an attacker rotates the
header to mint unlimited buckets (limit bypass), and the whole `client, proxy`
list becomes the "IP". The value must be parsed and trust-bounded.

## Decision 2 — Wire via `RATELIMIT_IP_META_KEY`, not new middleware

Set `RATELIMIT_IP_META_KEY = "apps.core.ratelimit.get_client_ip"`. The existing
`@ratelimit(key="ip", ...)` decorators are left **unchanged** — `_get_ip()`
routes through our callable automatically. One setting repairs IP keying for
all four current `key="ip"` limiters (2 in `companies`, 2 in `mailing`).

## Decision 3 — Do NOT rewrite global `REMOTE_ADDR`

A `SetRemoteAddrFromForwardedFor`-style middleware would change `REMOTE_ADDR`
for the *entire* request lifecycle (logging, Django internals, every app).
Only rate limiting needs the real IP, so the blast radius is kept to the
ratelimit key. `SECURE_PROXY_SSL_HEADER` (already conditionally set) is
unaffected and unrelated.

## Decision 4 — `RATELIMIT_FAIL_OPEN = True` (global)

These throttles are **abuse-prevention on read-only endpoints**, not a security
boundary. Failing closed converts a Redis hiccup into a site-wide outage; the
worst case of failing open is unthrottled reads during a (rare, short) cache
outage, which exposes only label strings and integer counts. `RATELIMIT_FAIL_OPEN`
is global, so it also covers the `mailing` limiters (unsubscribe / CV-link
flows) — equally acceptable: a cache outage should not block legitimate
unsubscribes. Documented here as a conscious trade-off.

Because `IGNORE_EXCEPTIONS = True` is already configured (see Context), this one
setting is sufficient end-to-end: with it, a Redis outage produces a `None`
counter, `get_usage()` returns `None`, `is_ratelimited()` returns `False`, and
the request is served — while `get_filter_options()` independently falls back
to a DB query. No change to the cache backend configuration is needed.

## Decision 5 — Externalise thresholds; raise defaults

| Setting | Env var | Default | Rationale |
|---|---|---|---|
| filter-options rate | `RATELIMIT_FILTER_OPTIONS` | `300/h` | Cacheable, cheap; generous even for office NAT |
| count rate | `RATELIMIT_FILTER_COUNT` | `600/h` | One per debounced filter change; absorbs heavy NAT |

Now keyed per *real* IP, these protect against a single hammering script while
never throttling normal humans. Decorators read the values from settings so
operators can tune without a code change. `block=True` is retained — exceeding
the limit still yields the friendly `429` from `RatelimitMiddleware`.

## Decision 6 — Client caching for `filter-options`

Emit `Cache-Control: public, max-age=300` on the `filter-options` response
(aligned with the 5-minute server-side Redis TTL). The taxonomy is identical
for every visitor, so a shared/public cache is correct and removes the
per-pageview hit entirely. The `count` response gets `Cache-Control: public,
max-age=60` (aligned with its 60 s server cache; the body is a query-keyed
integer, no per-user data). Server-side invalidation via `bust_filter_caches()`
is unchanged — a stale browser copy lasts at most one TTL, acceptable for a
taxonomy/counter.

## Decision 7 — `combobox.js` resilience

- `fetchOptions()` checks `r.ok` before `r.json()`; a non-OK response rejects.
- On failure, **do not** memoise the empty result: reset `optionsPromise` to
  `null` so a later trigger retries.
- Render a visible, inline, recoverable message inside the widget
  ("No se pudieron cargar las opciones. Reintentar") instead of dead empty
  dropdowns. Clicking retry re-runs `fetchOptions()`.
- The `count` fetch already checks `r.ok` and degrades to a dash / last-known
  value — keep as is.

## Decision 8 — Throttle observability

`RatelimitMiddleware.process_exception` already intercepts `Ratelimited`.
Add a `logger.warning("ratelimit: throttled path=%s ip=%s", request.path, ip)`
there. With Sentry installed, warning-level logs surface as breadcrumbs/events,
so a future throttling spike is visible without server-log access.

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| `TRUSTED_PROXY_HOPS` wrong → shared bucket returns, or spoofable | Default `1` matches current Coolify/Traefik; trust-bounded parsing + unit tests for short/extra/garbage XFF; documented for the CDN case |
| Trust model broken if gunicorn is reachable without going through Traefik | Precondition: the app port is only exposed on Coolify's internal Docker network, never published to the public internet — true for the current deployment; a client that could reach gunicorn directly could spoof `X-Forwarded-For` |
| Fail-open allows abuse during a cache outage | Endpoints expose only labels + counts; outages are rare/short; thresholds still apply once cache recovers |
| Stale browser cache hides a fresh import for ≤5 min | Acceptable for a slow-changing taxonomy; server-side bust unchanged |
| `RATELIMIT_IP_META_KEY` also changes `mailing` limiters | Intended fix — those were equally broken; covered by Task 1.5 audit |

## Verification (production, no code change, no log access)

1. `redis-cli -n 1 --scan --pattern 'rl:*'` — after the fix, distinct visitors
   produce distinct `rl:` keys (pre-fix: a single shared key near the cap).
2. Two-network test — exhaust the limit from network A; network B (different
   public IP) still receives `200`, proving independent buckets.
3. Confirm `Cache-Control` is present on `/api/companies/filter-options/`.
