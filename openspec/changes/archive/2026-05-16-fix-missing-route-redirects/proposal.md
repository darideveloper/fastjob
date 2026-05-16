# Change: Fix missing route redirects and add custom error handlers

## Why
Two routing gaps exist in the current codebase:

1. Visiting `/payments/` returns a 404 because no view is registered at the bare parent path — only sub-paths like `/payments/paquetes/` are handled.
2. The project has a well-structured `handler400` in `config/error_handlers.py` (XHR → JSON, browser → HTML, structured logging) but `handler404` and `handler500` are left as Django's built-in defaults, producing inconsistent error responses for API/AJAX callers and missing structured logging.

## What Changes
- Add a `RedirectView` at `""` in `apps/payments/urls.py` → `payment_packages` (HTTP 302, non-permanent)
- Add `handler404` to `config/error_handlers.py` following the existing `handler400` XHR/HTML split pattern
- Add `handler500` to `config/error_handlers.py` with the same XHR/HTML split (note: Django's 500 signature omits `exception`)
- Register `handler404` and `handler500` in `config/urls.py` (templates `404.html` and `500.html` already exist)
- Add tests for all three new behaviors

## Impact
- Affected specs: `pricing` (new routing requirement), `error-handling` (new capability)
- Affected code:
  - `apps/payments/urls.py` — one new `path()` entry
  - `config/error_handlers.py` — two new handler functions
  - `config/urls.py` — two new `handler*` assignments
  - `apps/payments/tests/` — new redirect test
  - `config/tests/` (or nearest test location) — new 404/500 handler tests
