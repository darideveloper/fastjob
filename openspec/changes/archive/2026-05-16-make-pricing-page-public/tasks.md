## 1. View Layer
- [x] 1.1 Remove `@login_required` decorator from `packages()` in `apps/payments/views.py`

## 2. Template — Conditional CTA
- [x] 2.1 In `templates/payments/packages.html`, wrap the existing `<form>` in `{% if user.is_authenticated %}` and add an `{% else %}` branch that renders an `<a href="/accounts/login/?next=/payments/paquetes/">` with identical button styling

## 3. Template — Nav Link for Anonymous Users
- [x] 3.1 In `templates/base.html` desktop cluster (`{% else %}` block, `hidden md:flex` div), add `<a href="/payments/paquetes/" …>Paquetes</a>` before the "Iniciar sesión" link
- [x] 3.2 In `templates/base.html` mobile drawer (`{% else %}` block, `#navbar-drawer` div), add the same "Paquetes" link before "Iniciar sesión"

## 4. Tests
- [x] 4.1 In `apps/payments/tests/`, add a test asserting that `GET /payments/paquetes/` returns HTTP 200 for an anonymous client
- [x] 4.2 Add a test asserting that the anonymous response HTML contains `href="/accounts/login/?next=/payments/paquetes/"` and does NOT contain `action="` pointing to `create_checkout`
- [x] 4.3 Add a test asserting that the authenticated response still contains the `<form>` pointing to `create_checkout`
