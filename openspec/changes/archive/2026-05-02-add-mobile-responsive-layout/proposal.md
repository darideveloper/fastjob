# Change: Add mobile-responsive layout to the public app shell, landing, and dashboard

## Why

A multi-viewport audit (320 / 375 / 768 / 1024 / 1440 px) revealed that the
authenticated and anonymous experience both break on common phone widths.
Every issue traces back to one of two root causes:

1. **The global navbar in `templates/base.html` is a single nowrap flex row
   with no breakpoint-aware collapse.** Once the right-hand cluster (credits
   chip, "Panel", "Comprar", "Salir" — or "Iniciar sesión" + "Empezar gratis"
   for anonymous visitors) exceeds the viewport, the `max-w-7xl` container
   pushes `<body>` wider than `window.innerWidth`. Measured on 320 px,
   logged-in `document.documentElement.scrollWidth` is **421 px** (a 101 px
   horizontal overflow). This bleeds into every page that extends `base.html`
   — dashboard, packages, success, login, cv_not_found, unsubscribe,
   delete-account.
2. **Per-page templates assume desktop widths in a few places** — the
   dashboard activity table never triggers its `overflow-x-auto` because the
   inner `<table class="w-full">` collapses to fit (causing 6-line cells and
   clipped status badges); CV-list rows place actions side-by-side with a
   long title; landing hero CTAs use `px-8 py-4 text-lg` which forces 2-line
   wrap on 320 px.

While auditing, we also surfaced one functional regression: **`GET
/accounts/login/` returns HTTP 500 with `NoReverseMatch: Reverse for
'account_signup' not found`.** The C3 security hardening
(`config/urls.py:8-11`) deliberately mounts only the OAuth subset of allauth,
but `allauth.account.views.LoginView.get_context_data()` unconditionally
calls `reverse('account_signup')` to populate `signup_url` in template
context. The custom template at `templates/account/login.html` never uses
that URL and renders correctly — only the missing URL **name** is the
problem.

Both classes of issue are user-blocking on mobile (≥ 60 % of organic traffic
for SaaS landing pages of this shape) and on the login page (100 % of
non-OAuth-button entries crash). They should ship together because the login
fix is what unblocks audited verification of the responsive login layout.

## What Changes

### 1. Global app shell (NEW capability `ui-shell`)

- **Mobile-collapsing navbar.** The right-hand cluster collapses behind a
  hamburger button below the `md` breakpoint (640 px → 768 px). The drawer
  reveals the same links plus the credits chip stacked vertically. Above
  `md`, the existing horizontal layout is preserved exactly.
- **No horizontal overflow at any viewport ≥ 320 px.** Across every template
  that extends `base.html`, `document.documentElement.scrollWidth` MUST equal
  `window.innerWidth` on 320 / 360 / 375 / 414 px.
- **Footer copyright wraps gracefully** (already mostly correct — verified).

### 2. Landing page (MODIFIED capability `landing`)

- Hero CTAs (`Empezar con Google` / `Empezar con Microsoft`) get smaller
  padding and font sizes below `sm` so they fit on one line at 320 px.
- The "Ver paquetes y empezar" CTA below the company-finder section gets the
  same treatment.
- The `<br class="hidden sm:block"/>` in the hero `<h1>` is left as-is
  (already correct — only flagged as cosmetic in the audit).

### 3. Dashboard (MODIFIED capability `dashboard`)

- **Activity table.** Add `min-w-[640px]` (or a documented equivalent) on
  `<table>` so the existing `overflow-x-auto` wrapper actually engages on
  small viewports. Status badges no longer get clipped.
- **CV-list rows.** Stack title + actions vertically below `sm` (`flex
  flex-col sm:flex-row`) so neither side eats the other on long CV names.
- **Credit-card stat link row** (`Comprar más` + `Facturación`) becomes
  `flex-wrap` so it never overflows the card on cramped widths.
- **`<input type="file">`** is replaced by a styled label (sr-only input)
  for visual consistency in Spanish locale (browser-native "Choose File" /
  "No file chosen" labels were ignoring the design system).

### 4. Account login fix (NEW capability `accounts`)

- Mount a no-op named URL `account_signup` that returns `302 →
  account_login`, so allauth's `LoginView.get_context_data()` resolves
  successfully. This preserves the C3 OAuth-only posture (no signup form,
  no password endpoints) while restoring `GET /accounts/login/` to HTTP
  200.

## Impact

- **Affected specs:**
  - `ui-shell` (NEW) — mobile navbar collapse, no-overflow invariant.
  - `dashboard` (ADDED requirements) — activity table overflow, CV-list
    row stacking, stat-card link wrap, styled file input.
  - `landing` (ADDED requirements) — hero CTA sizing on small viewports.
  - `accounts` (NEW) — login page does not 500, signup URL name resolves to
    a redirect.
  - No requirements removed. No matching-semantics or API-contract
    changes.

- **Affected code:**
  - `templates/base.html` — navbar refactor (hamburger button + drawer
    `<div>`); a tiny inline JS toggle (~10 lines) or Alpine.js sprinkle
    (already-discussed alternative in `design.md`).
  - `templates/dashboard/index.html` — activity table `min-w-[640px]`,
    CV-list row stacking, stat-card link wrap, file-input label.
  - `templates/home.html` — hero / company-finder CTA responsive sizing.
  - `templates/dashboard/delete_account.html` — minor button-row stacking
    on mobile (defensive UX win against accidental destructive taps).
  - `config/urls.py` — add `path("accounts/signup/", RedirectView..., name="account_signup")`.
  - `apps/accounts/tests/` — one new functional test that
    `GET /accounts/login/` returns 200.
  - One new responsive smoke test under `apps/dashboard/tests/` (or a
    dedicated `tests/responsive/`) that asserts no horizontal overflow on
    the dashboard at 320 px (Playwright-driven, marked `@pytest.mark.slow`
    to mirror the existing convention noted in `openspec/project.md`).

- **No new dependencies.** The hamburger toggle uses ~10 lines of inline
  vanilla JS (no Alpine.js / no Tailwind plugin). Tailwind utility classes
  used (`md:hidden`, `md:flex`, `flex-wrap`, `min-w-[640px]`, `truncate`,
  `sr-only`) are all available in the existing CDN build.

- **Operational:**
  - No DB changes, no Celery changes, no env-var changes.
  - One new public URL (`/accounts/signup/`) that 302-redirects to
    `/accounts/login/`. This is a defensive shape: any agent or stale
    bookmark that hits the historical signup URL now lands on the OAuth
    login page instead of crashing.

- **Backwards compatibility:**
  - Desktop (≥ md) layout unchanged across every page audited.
  - No URL renamed / removed; only one added.
  - No template variables added or removed in `base.html` (so any other
    extender keeps working).
