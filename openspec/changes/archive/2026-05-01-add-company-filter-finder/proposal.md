# Change: Replace free-text filters with DB-backed dropdowns + live company-match counter (dashboard & landing)

## Why

The dashboard's "Sector / Área" and "Ubicación" inputs at `apps/dashboard/views.py:115` are free-text fields. Users have no way to know which sectors/locations are actually represented in the company database, so they routinely pick filter values that match **zero** companies — and then sit confused while the slow-drip engine sends nothing. There is also no public-facing way for prospects on the landing page to validate that FastJob's database actually covers their target market before they pay.

Two problems, one root cause: the filters are decoupled from the underlying `Company` table.

## What Changes

1. **Dropdowns sourced from the DB.** The dashboard's two text inputs become searchable dropdowns whose option lists are generated from the `DISTINCT` non-empty values of `Company.area` and `Company.location`. Users can only pick values that actually exist in the database. Empty selection means "no filter on this field".

2. **Live company-match counter (dashboard).** Below the filter form, a counter shows the number of companies matching the current selection. It updates whenever either field changes (debounced). The counter shows **only** an integer — never any company name, email, or row data.

3. **New public company-finder section on the landing page.** Same two dropdowns + counter, positioned just above the call-to-action that links to the pricing/packages page (see open question in `design.md`). 100% functional without login. Same data source, same UI behavior, same security posture as the dashboard widget.

4. **New public-but-rate-limited HTTP API under `apps/companies/`** with two endpoints:
   - `GET /api/companies/filter-options/` → `{"areas": [...], "locations": [...]}`
   - `GET /api/companies/count/?area=…&location=…` → `{"count": N}`

   No authentication required (so the landing page can call them anonymously), but per-IP rate-limited and **structurally incapable of returning company-identifying data** — the only fields ever serialized are aggregate counts and option labels.

5. **BREAKING — matching semantics change from `__icontains` to `__iexact`.** Today the mailing engine at `apps/mailing/tasks.py:60-63` matches user filters against `Company.area` / `Company.location` with case-insensitive substring matching. Once the UI restricts users to exact DB values, the engine MUST use exact matching too — otherwise the live counter on the dashboard would lie about what the engine is actually going to send. A one-time data migration normalizes any existing `User.area_filter` / `User.location_filter` values that don't match a current DB option (clearing them rather than silently misbehaving).

## Impact

- **Affected specs (all new):**
  - `companies` — public filter API (options endpoint + count endpoint).
  - `dashboard` — search-filter widget behavior (now dropdowns + live counter).
  - `landing` — new anonymous company-finder section.
  - `mailing` — filter matching switches from substring to exact (breaking).

- **Affected code:**
  - `apps/companies/` — new `views.py`, `urls.py`, mounting under `config/urls.py`. New cache layer (Redis is already configured per `openspec/project.md`).
  - `apps/dashboard/views.py` — `update_filters` validates POSTed values against the allowed-options whitelist.
  - `apps/dashboard/index.html` (template) — filter form rewritten as combobox + counter.
  - `apps/mailing/tasks.py:60-63` — `__icontains` → `__iexact`.
  - `templates/home.html` — new section between Trust Signals and footer (or wherever the "plans" section ends up living on the landing page).
  - `apps/accounts/migrations/` — one data migration to normalize stale `area_filter` / `location_filter` values on existing users.
  - Tests in `apps/companies/tests/`, `apps/dashboard/tests/`, `apps/mailing/tests/test_tasks.py` (existing test at line 100 will need updating for the matching-semantics change).

- **Operational:**
  - One new cache namespace (filter options + count); 5-minute TTL keeps Redis pressure trivial.
  - Two new public URL paths under `/api/companies/` — if any reverse-proxy WAF rules whitelist URL prefixes, ops will need to extend them.

- **No new dependencies.** Combobox is vanilla JS; rate-limiting reuses `django-ratelimit` already pinned in `requirements.txt:21`.
