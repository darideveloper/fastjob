## Context

The system already stores per-company `area` and `location` as free-text strings on `Company` (`apps/companies/models.py:5-19`). The mailing engine matches the user's free-text filters against these columns with `__icontains` (`apps/mailing/tasks.py:60-63`), and there is no UI affordance that tells users which values would actually match real rows. The asymmetry between "what the user types" and "what's in the DB" is the source of the silent-zero-match problem this change targets.

A second driver is conversion on the landing page: anonymous visitors can't validate FastJob's market coverage before paying. A live counter that says "428 companies match Tecnología + Madrid" is much more compelling than a static feature list — but only if it is **provably safe** to expose anonymously, since the underlying table is the company asset.

Stakeholders:
- **Job-seeker users**: want to know up front whether their filters match anything.
- **Anonymous prospects**: want to see market coverage before purchasing.
- **Ops / data team**: own the company table and need confidence that the public endpoint cannot exfiltrate names, emails, or row IDs.

Constraints from `openspec/project.md` and the existing codebase:
- Stack is Django 4.2 + DTL + Tailwind via CDN — no JS framework, no SPA build pipeline.
- Redis is already wired (`task queue & cache, separate Redis DBs`), so caching is free.
- `django-ratelimit==4.1.0` is already in use (`apps/mailing/views.py:18`, `apps/dashboard/views.py:259`).
- Spanish-localized UI (`LANGUAGE_CODE=es`) — copy in templates must be Spanish.

## Goals / Non-Goals

**Goals**
- Make the dashboard filters honest: the user can only pick values that exist in the DB, and the counter shows exactly the number of companies the engine would consider for their next send.
- Add a parallel anonymous experience on the landing page that converts curiosity into pricing-page visits, without leaking any company-identifying data.
- Keep the implementation small and boring: vanilla JS combobox, Django views, Redis cache, no new dependencies.

**Non-Goals**
- Building a CRUD admin for `JobArea` / `Location` lookup tables. We deliberately do **not** introduce normalized lookup models — distinct values from the existing `Company` rows are sufficient and avoid a data migration.
- Multi-select filters or boolean operators (e.g. "Tecnología OR Diseño"). One value per field, matching the current data model.
- Showing per-company detail anywhere on the public surface.
- Changing the company-import flow (`apps/companies/importers.py`).
- Pagination, faceting, or analytics on the count.

## Decisions

### Decision 1: Source dropdown options from `Company.objects.values_list(..., flat=True).distinct()`, not a new lookup model

**What**: The "options" endpoint runs `Company.objects.exclude(area="").values_list("area", flat=True).distinct().order_by("area")` (and same for `location`), case-folded and de-duplicated in Python before serializing.

**Why**:
- The user explicitly said the options should "match the data in the companies model". Adding a `JobArea` FK introduces a data migration, an admin maintenance burden, and a window where importer-created companies have an `area` string that doesn't yet exist in the lookup table.
- Distinct queries on `area` / `location` are trivially indexable if needed later (current row count is small; postpone the index until we have evidence we need it).
- The set of distinct values is the source of truth — if the importer adds new sectors, they appear automatically.

**Alternatives considered**:
- *Introduce `JobArea` and `Location` models with FKs from `Company`*: cleaner long-term but adds a 1.5-day data-migration scope and an admin UI just to maintain something the importer already produces. Rejected as premature normalization.
- *Hardcode an enumeration in code*: rejected — drift between code and DB is exactly the bug we're fixing.

### Decision 2: Two endpoints, both anonymous + IP-rate-limited, structurally count-only

**What**:
- `GET /api/companies/filter-options/` returns `{"areas": [...], "locations": [...]}` — sorted, distinct, non-empty strings only. Cached in Redis for 5 minutes (key: `companies:filter-options:v1`).
- `GET /api/companies/count/?area=…&location=…` returns `{"count": <int>}`. Both query params optional. Cached in Redis for 60 seconds (key: `companies:count:v1:{sha1(area|location)}`).

**Why**:
- Anonymous access is required for the landing page. Splitting into two endpoints (instead of one combo endpoint) keeps each cache key tight and lets the options-list cache live much longer than the count cache (options change rarely; count is more dynamic via `last_received_at` shifts and admin imports).
- Returning **only** integers + label strings means there is no code path on either endpoint that ever touches `Company.email`, `Company.name`, or `Company.id`. Even an SSRF-style probe cannot reveal company-identifying data because the serializer simply has no field for it.
- IP rate-limit (e.g. `60/h` on count, `30/h` on options) bounds enumeration cost. A determined attacker could in principle bisect filter combinations to estimate distribution, but the only thing they'd learn is what `Company.area` / `Company.location` *labels* exist — which we are publishing intentionally — and a count, which is non-identifying.

**Alternatives considered**:
- *Require login*: would block the landing-page use case, which is the higher-value half of this change.
- *Sign the options list and embed it in HTML*: keeps the count private but means the options list can drift from the current DB state until cache invalidation; also breaks "only allow options from the database" for users whose page was rendered hours ago.
- *POST + CSRF*: GET is correct here — these endpoints are idempotent reads. CSRF is irrelevant for a same-origin GET that returns no state-changing data.

### Decision 3: Validate POSTed `area_filter` / `location_filter` against the same allowed-options whitelist

**What**: `apps/dashboard/views.py:115` (`update_filters`) is changed to reject any POSTed value that isn't in the current options list. Invalid values produce a `messages.error` and the filter is **not** updated.

**Why**: The dropdown is client-side; a hostile or buggy client can POST any string. Without server-side validation we'd reintroduce the original bug (filters that match zero rows) by a different route, plus we'd allow free-text injection into a column we now treat as enum-shaped.

### Decision 4: BREAKING — matching switches from `__icontains` to `__iexact`

**What**: `apps/mailing/tasks.py:60-63` changes `area__icontains=...` → `area__iexact=...` (same for location). The dashboard counter and the mailing engine use the same query helper (a new `apps/companies/queries.py:matching_companies_qs(area, location)`) so they cannot drift.

**Why**: With dropdowns of exact values, `__icontains` is a footgun: a filter of "Diseño" would also match a company whose area is "Diseño Industrial", inflating the counter relative to the user's intent. Worse, it would mean "the engine sent your CV to companies you didn't pick". `__iexact` is what users will reasonably expect once the UI is dropdown-shaped.

**Migration**: A data migration walks every `User` row and sets `area_filter = ""` / `location_filter = ""` if the current value does not appear (case-insensitively) in `Company.area` / `Company.location`. Users whose filters survive the migration are unaffected. Users whose filters are cleared see "no filter" until they pick from the new dropdowns — strictly better than the current "filter that silently matches zero rows" state.

**Alternatives considered**:
- *Keep `__icontains` and live with counter inaccuracy*: rejected — defeats the purpose of the counter.
- *Allow free-text + dropdown*: rejected — doubles the surface area for tests and the user's "only allow options from the database" requirement explicitly excludes it.

### Decision 5: Vanilla JS combobox, no new dependency

**What**: A small (<150 LOC) vanilla JS component renders an `<input type="text">` plus a filtered `<ul>` of options it fetches once from `/api/companies/filter-options/`. Typeahead filters client-side; selecting a row writes to the input and to a hidden `<input type="hidden" name="area_filter">` that the form submits. The same component is reused on the landing page (no form submit there — just triggers the count fetch).

**Why**:
- The codebase has no JS framework. Adding one for two combo boxes is overkill.
- All options fit comfortably in a single payload (the company table is curated, not user-generated; even at 10× growth it's <100 KB).
- Using `<datalist>` was considered but its UX is inconsistent across browsers (no styling, can't show "no matches", behaves oddly on mobile).

### Decision 6: Cache invalidation on company writes

**What**: A `post_save` / `post_delete` signal on `Company` busts both `companies:filter-options:v1` and the count-cache namespace (delete pattern `companies:count:v1:*`). The bulk import path (`apps/companies/importers.py`) wraps its work in a `transaction.on_commit(...)` that does the bust once per import, not per row.

**Why**: A 5-minute stale options list is acceptable for normal browsing but very confusing right after an admin import. Bust-on-write keeps the worst-case staleness to one request.

## Risks / Trade-offs

- **Risk**: Distinct values include label noise (e.g. `"Tecnología"`, `"tecnología"`, `" Tecnología "` as three separate options).
  → **Mitigation**: Normalize on read (`strip()` + collapse whitespace; case-fold for de-dup but preserve the canonical casing of the most-frequent occurrence). Long-term fix is at the import layer, out of scope for this change.

- **Risk**: Enumeration via the count endpoint reveals market segmentation that competitors could use.
  → **Mitigation**: This is a **deliberate** disclosure — it is the entire point of the landing-page widget. Rate limit blunts automation; counts are non-identifying. If ops later judges this too disclosive, we can ship a "round to nearest 10" obfuscator behind a flag. Not implementing speculatively.

- **Risk**: The `__icontains` → `__iexact` change silently widens or narrows what users get sent to.
  → **Mitigation**: Data migration normalizes existing filters to either an exact match or empty. Release notes call it out. Pre-existing test at `apps/mailing/tests/test_tasks.py:100` is updated to assert the new semantics.

- **Trade-off**: We rebuild the options list on cache miss with a `DISTINCT` query rather than maintaining a denormalized table. At current scale this is sub-millisecond; if the company table grows past ~100k rows we may want a materialized view or a real lookup table. Re-evaluate then.

- **Trade-off**: Server-side validation of dropdown values rejects POSTs with stale options (e.g. user had the page open for an hour, an admin removed an area, user submits). The error message is friendly but the filter is dropped. Acceptable — alternative is silently re-mapping, which violates the "only allow options from the database" rule.

## Migration Plan

1. Ship the new endpoints, signals, and cache layer behind no flag (read-only, additive).
2. Ship the data migration that normalizes existing `User.area_filter` / `User.location_filter` against the allowed options. This must run **before** the engine switch — otherwise users with stale filters would see a sudden zero-send window.
3. Ship the engine change (`__icontains` → `__iexact`) and the dashboard UI in the same release as step 2.
4. Ship the landing-page section.
5. **Rollback**: revert order is 4 → 3 → 2 → 1. The data migration is forward-only (it clears strings); rollback would not restore them, but since the previous behavior also silently matched zero rows for those strings, no user-visible regression.

## Open Questions

- **Q1 (placement on landing page).** The current `templates/home.html` does not contain a "plans" section — pricing lives on a separate page at `/payments/paquetes/`. The user's request says "in the landing page, before the plans". Two interpretations:
  - (a) Add a "Plans" / pricing section to the landing page in this same change, with the new finder section just above it.
  - (b) Treat the existing CTA buttons that link to `/payments/paquetes/` as the "plans" reference, and place the finder above the bottom CTA.

  Default in this proposal: **(b)**, position the new section between "Trust Signals" and a new "¿Listo? Elige tu paquete" CTA block that links to `/payments/paquetes/`. Confirm with user during review.

- **Q2 (options canonicalization).** Some imported companies have whitespace or casing variants in `area` / `location`. Should the data-cleanup of those values be in scope, or strictly limited to read-side normalization? Default: read-side only (Decision 6 mitigation); flag a follow-up ticket for import-side cleanup.

- **Q3 (counter on hover / on submit).** On the dashboard, should the counter update live as the user types in the combobox (every selection), or only after they hit "Guardar filtros"? Default: live update on every selection — that's the whole point of the counter. The "Guardar filtros" button still persists the choice for the engine.
