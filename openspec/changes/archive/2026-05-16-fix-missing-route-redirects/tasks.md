## 1. Payments Root Redirect
- [x] 1.1 In `apps/payments/urls.py`, prepend `path("", RedirectView.as_view(pattern_name="payment_packages", permanent=False), name="payments_root")` as the first `urlpatterns` entry (import `RedirectView` from `django.views.generic`)
- [x] 1.2 Verify manually (or via `python manage.py show_urls`) that `GET /payments/` now appears in the routing table
- [x] 1.3 In `apps/payments/tests/test_packages_view.py`, add a test asserting that `GET /payments/` returns HTTP 302 with `Location: /payments/paquetes/`

## 2. Custom 404 Handler
- [x] 2.0 Create `config/tests/__init__.py` (empty) to establish the test package for config-level tests
- [x] 2.1 In `config/error_handlers.py`, add `handler404(request, exception, template_name="404.html")` following the same `_is_xhr` split as `handler400`: XHR → `JsonResponse({"error": "..."}, status=404)`, browser → render `404.html` via `loader.get_template`
- [x] 2.2 Register `handler404 = "config.error_handlers.handler404"` in `config/urls.py` (alongside the existing `handler400` assignment)
- [x] 2.3 In `config/tests/test_error_handlers.py`, add a test asserting that a nonexistent URL returns 404 with `Content-Type: text/html` for a regular browser request
- [x] 2.4 In `config/tests/test_error_handlers.py`, add a test asserting the same nonexistent URL returns 404 with `Content-Type: application/json` when `HTTP_X_REQUESTED_WITH=XMLHttpRequest` is set

## 3. Custom 500 Handler
- [x] 3.1 In `config/error_handlers.py`, add `handler500(request, template_name="500.html")` — note Django's 500 handler signature does NOT include `exception`; use `_is_xhr` for the same split: XHR → `JsonResponse({"error": "Error interno del servidor."}, status=500)`, browser → render `500.html`
- [x] 3.2 Register `handler500 = "config.error_handlers.handler500"` in `config/urls.py`
- [x] 3.3 In `config/tests/test_error_handlers.py`, add a test asserting the custom 500 handler returns HTTP 500 with `Content-Type: text/html` for browser requests — set `client.raise_request_exception = False` (or use `@override_settings(DEBUG=False)` with a test-only raising view) since Django's test client re-raises exceptions by default instead of routing them to `handler500`
- [x] 3.4 In `config/tests/test_error_handlers.py`, add a test asserting the custom 500 handler returns HTTP 500 with `Content-Type: application/json` for XHR requests (same `raise_request_exception = False` pattern)
