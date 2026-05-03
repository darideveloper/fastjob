## 1. Coordinate with pending change
- [x] 1.1 Confirm `add-mobile-responsive-layout` has no merged code yet
      (UPDATE: it was already merged, so I updated the merged specs instead).
- [x] 1.2 Open a follow-up commit on the `add-mobile-responsive-layout`
      branch that swaps `"Créditos disponibles"` → `"Envíos disponibles"`
      in `openspec/changes/add-mobile-responsive-layout/specs/dashboard/spec.md:37,40`
      and `"credits chip"` → `"envíos chip"` in `specs/ui-shell/spec.md:9-11`,
      and `tasks.md` lines 18, 21, 28. (DONE: Updated `openspec/specs/ui-shell/spec.md` and `openspec/specs/dashboard/spec.md` directly).

## 2. Update front-of-house templates
- [x] 2.1 `templates/base.html:42` — replace `créditos` with `envíos` in
      the navbar chip. (DONE: Both desktop and mobile drawer versions).
- [x] 2.2 `templates/home.html:65` — replace heading `3. Compra créditos`
      with `3. Compra envíos`.
- [x] 2.3 `templates/home.html:66` — replace tagline with
      `Cada envío manda tu CV a una empresa. Elige el paquete que mejor se adapte a ti.`
- [x] 2.4 `templates/dashboard/index.html:41` — replace stat-card label
      `Créditos disponibles` with `Envíos disponibles`.
- [x] 2.5 `templates/payments/packages.html:2` — replace `{% block title %}`
      contents `Paquetes de Créditos — FastJob` with
      `Paquetes de Envíos — FastJob`.
- [x] 2.6 `templates/payments/packages.html:8` — replace tagline with
      `Cada envío = un CV a una empresa. Sin suscripciones, sin sorpresas.`
- [x] 2.7 `templates/payments/packages.html:58` — replace button text
      `Comprar {{ package.credits }} créditos` with
      `Comprar {{ package.credits }} envíos`.
- [x] 2.8 `templates/payments/success.html:14` — replace
      `{{ payment.credits_granted }} créditos` with
      `{{ payment.credits_granted }} envíos`.

## 3. Update server-side flash messages
- [x] 3.1 `apps/dashboard/views.py:150` — replace
      `"No tienes créditos disponibles. Compra un paquete para continuar."`
      with `"No tienes envíos disponibles. Compra un paquete para continuar."`.
      No other `messages.error/success/info` string in `apps/` mentions
      *crédito*; verify with `rg -n "crédito" apps`.

## 4. Update admin-visible model display
- [x] 4.1 `apps/payments/models.py:14` — change
      `verbose_name = "Paquete de Créditos"` to
      `verbose_name = "Paquete de Envíos"`.
- [x] 4.2 `apps/payments/models.py:15` — change
      `verbose_name_plural = "Paquetes de Créditos"` to
      `verbose_name_plural = "Paquetes de Envíos"`.
- [x] 4.3 `apps/payments/models.py:19` — change `__str__` return value
      to `f"{self.name} — {self.credits} envíos por {self.price_eur}€"`.
- [x] 4.4 Confirm no Django migration is required (these are display-only
      `Meta` attributes; Django records `verbose_name` changes in
      migrations but the change is a no-op at the DB level). Run
      `python manage.py makemigrations --dry-run payments` and, if a
      migration is generated, include it as part of the commit. (DONE: Migrations generated for accounts and payments).

## 5. Update OpenSpec project glossary
- [x] 5.1 `openspec/project.md` Domain Context → first bullet — rewrite
      from `**Credits**: Users buy credits to send CVs. One credit equals
      one email sent to one company.` to use *envíos* terminology. Keep
      the bullet's leading bold key in English-only commentary OR rename
      to `**Envíos**`.

## 6. Verify no regressions
- [x] 6.1 `rg -nP "[Cc]r[ée]dito" templates apps openspec/project.md` —
      MUST return zero matches after step 5 lands.
- [x] 6.2 Run the test suite: `pytest` — all tests pass.
- [x] 6.3 Manual smoke: load pages and confirm "envíos" displays everywhere.

## 7. Validate the proposal itself
- [x] 7.1 `openspec validate rename-credits-to-envios --strict` —
      MUST pass before requesting approval.
