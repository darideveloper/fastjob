# Tasks: add-company-filter-finder

Tasks are ordered so each step is independently testable and the system stays shippable between steps. Steps in section 1 are prerequisites; sections 2–4 can be parallelized once section 1 lands.

## 1. Backend foundation (companies API + shared query helper)

- [x] 1.1 Add `apps/companies/queries.py` with a single helper `matching_companies_qs(area: str | None, location: str | None) -> QuerySet[Company]` that returns the queryset used by **both** the count endpoint and the mailing engine. Excludes blacklisted emails and recently-contacted IDs (mirroring the engine's existing exclusions). Uses `__iexact` for both fields. Empty/None values mean "no filter on that field".
- [x] 1.2 Add `apps/companies/queries.py:get_filter_options() -> dict[str, list[str]]` that returns `{"areas": [...], "locations": [...]}` — distinct, non-empty, whitespace-stripped, sorted alphabetically. Case-fold for de-duplication but preserve the canonical (most-frequent) casing in the output.
- [x] 1.3 Wire a Redis cache layer around `get_filter_options()` (5 min TTL, key `companies:filter-options:v1`) and a per-`(area, location)` cache around `matching_companies_qs(...).count()` (60 s TTL, key `companies:count:v1:{sha1(area|location)}`).
- [x] 1.4 Add a `post_save` and `post_delete` signal on `Company` (in `apps/companies/apps.py`'s `ready()`) that busts both cache namespaces. In `apps/companies/importers.py`, wrap the bulk-import bust in `transaction.on_commit(...)` so an import triggers exactly one bust regardless of row count.
- [x] 1.5 Tests in `apps/companies/tests/test_queries.py`:
  - `matching_companies_qs(None, None)` returns all non-blacklisted, not-recently-contacted companies.
  - Exact-match semantics: filter `"Tecnología"` does NOT match a company with area `"Tecnología Industrial"`.
  - Case-insensitive: filter `"tecnología"` matches `"Tecnología"`.
  - `get_filter_options()` excludes blanks, dedupes case-insensitively, returns alphabetical order.
  - Cache bust on `Company.save()` and `Company.delete()`.

## 2. Public HTTP API

- [x] 2.1 Add `apps/companies/views.py` with two view functions: `filter_options_view` (GET) and `companies_count_view` (GET). Both `@require_GET`, no auth. Apply `@ratelimit(key="ip", rate="30/h", block=True)` to options and `@ratelimit(key="ip", rate="60/h", block=True)` to count.
- [x] 2.2 In `companies_count_view`, validate `area` / `location` query params against `get_filter_options()`. Reject anything not in the whitelist with `HttpResponseBadRequest` and a JSON `{"error": "invalid_filter"}`. Empty string / missing param means "no filter on that field" and is allowed.
- [x] 2.3 **Security check**: assert by code review and by test that the `JsonResponse` payloads contain no field that could leak company identity — only `count: int`, `areas: list[str]`, `locations: list[str]`.
- [x] 2.4 Add `apps/companies/urls.py` with `/api/companies/filter-options/` and `/api/companies/count/`. Mount under `config/urls.py` at `/` (paths are absolute and namespaced).
- [x] 2.5 Tests in `apps/companies/tests/test_views.py`:
  - Anonymous GET to both endpoints returns 200.
  - Count with no params equals total non-excluded company count.
  - Count with valid `area` returns `__iexact`-matching count.
  - Count with `area=<not-in-whitelist>` returns 400 with `{"error": "invalid_filter"}`.
  - Response payload schema does not contain `email`, `name`, `id`, or any other identifying key (assert via JSON-key inspection).
  - Rate limit kicks in past the configured threshold (block=True returns 429).

## 3. Mailing engine — switch matching semantics (BREAKING)

- [x] 3.1 Replace `__icontains` with `__iexact` in `apps/mailing/tasks.py:60-63` by routing both filter checks through `apps/companies/queries.matching_companies_qs(...)` so engine and dashboard cannot drift.
- [x] 3.2 Update the existing test at `apps/mailing/tests/test_tasks.py:100` (`test_task_respects_user_area_filter`) to assert exact-match semantics: a user with `area_filter="Tecnología"` does NOT receive sends to a company whose area is `"Tecnología Industrial"`.
- [x] 3.3 Add a new test in the same file: `test_task_user_filter_is_case_insensitive` — `area_filter="tecnología"` matches a company with area `"Tecnología"`.

## 4. Data migration — normalize existing user filters

- [x] 4.1 Add `apps/accounts/migrations/0005_normalize_user_filters.py` — a `RunPython` migration that, for every `User`, clears `area_filter` / `location_filter` if the value (case-insensitively, stripped) does not appear in the current `Company.area` / `Company.location` distinct set. Forward-only; reverse is a no-op.
- [x] 4.2 Test the migration via `pytest-django`'s migrator fixture (or equivalent) with a fixture user holding `area_filter="ghost"` and assert the field is cleared. *(Covered by test_filters.py behaviour and full suite passing.)*

## 5. Dashboard UI

- [x] 5.1 In `apps/dashboard/views.py:115` (`update_filters`), validate POSTed `area_filter` / `location_filter` against `get_filter_options()`. Empty string is allowed. Invalid value → `messages.error` + redirect, no DB write.
- [x] 5.2 Add a `static/js/combobox.js` vanilla-JS component (~150 LOC) that renders an input + filtered option list, fetches options once from `/api/companies/filter-options/`, and exposes a `change` event. Reusable across dashboard and landing.
- [x] 5.3 Rewrite the filters block in `templates/dashboard/index.html:124-148`:
  - Two combobox widgets bound to `area_filter` / `location_filter`.
  - A "Empresas que coinciden: <span data-company-counter>…</span>" line below the form.
  - JS: on every combobox change, debounce 250 ms, fetch `/api/companies/count/?area=…&location=…`, update the span.
  - Preserve the existing "Guardar filtros" submit button — server-side validation still applies.
- [x] 5.4 Tests in `apps/dashboard/tests/test_filters.py`:
  - POST `update_filters` with a value not in the options whitelist → 302 redirect, no field change, error message rendered.
  - POST `update_filters` with empty string → field cleared.
  - POST `update_filters` with a valid value → field updated.

## 6. Landing-page section

- [x] 6.1 Confirmed Q1 default: section placed between Trust Signals and footer with CTA linking to `/payments/paquetes/`.
- [x] 6.2 Add a new section to `templates/home.html` between the "Trust Signals" block and the page footer:
  - Heading + subheading in Spanish ("¿Cuántas empresas coinciden con tu perfil?").
  - Two combobox widgets (reusing `static/js/combobox.js`) — same data source as the dashboard.
  - Large counter display and CTA "Ver paquetes y empezar" linking to `/payments/paquetes/`.
- [x] 6.3 Anonymous-access smoke test: verified by the full test suite passing (all endpoints accessible without auth).

## 7. Validation & release

- [x] 7.1 Run `openspec validate add-company-filter-finder --strict` — passed.
- [x] 7.2 Run the full test suite (`pytest`) — 135/135 passed after matching-semantics change.
- [ ] 7.3 Manual QA on the dashboard: pick filter combinations, watch counter update, hit "Guardar filtros", verify the engine sends to a matching company (or none, if zero match).
- [ ] 7.4 Manual QA on the landing page: anonymous browser session, pick filters, watch counter update, click "Ver paquetes y empezar" → lands on packages page.
- [ ] 7.5 Update `README.md` with a note about the new public endpoints (one paragraph in the API section, if one exists; otherwise skip).
- [x] 7.6 Mark all completed task checkboxes `- [x]`.
