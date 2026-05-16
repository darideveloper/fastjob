# Change: Make Pricing Page Public

## Why
The `/payments/paquetes/` page is currently gated behind `@login_required`, meaning anonymous visitors are redirected to login before they can see plan options or prices. This reduces conversion from organic traffic and breaks the natural "see pricing → decide → register" user flow.

## What Changes
- Remove `@login_required` from the `packages` view so any visitor can access `/payments/paquetes/`.
- In `templates/payments/packages.html`, replace the checkout `<form>` with a login-redirect `<a>` link (same button styling) when the user is not authenticated. Authenticated users retain the existing POST-to-Stripe flow unchanged.
- In `templates/base.html`, add a "Paquetes" nav link for anonymous users in both the desktop cluster (`{% else %}` block) and the mobile drawer (`{% else %}` block), placed between the logo area and the "Iniciar sesión" / "Empezar gratis" links.

## Impact
- Affected specs: `pricing`, `ui-shell`
- Affected code:
  - `apps/payments/views.py` — remove `@login_required` decorator from `packages()`
  - `templates/payments/packages.html` — conditional button rendering based on `user.is_authenticated`
  - `templates/base.html` — add pricing link to anonymous nav sections (desktop + mobile drawer)
