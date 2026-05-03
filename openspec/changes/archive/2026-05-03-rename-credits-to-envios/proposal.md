# Change: Rename user-visible "créditos" terminology to "envíos"

## Why
Users buy "créditos" today, but the product's actual unit-of-value is **one CV
sent to one company** (see `openspec/project.md` Domain Context). The current
copy already half-acknowledges this: `templates/home.html:66` reads
*"Cada crédito equivale a un envío"* — the landing page literally translates
the term it's selling. Calling the unit what it is — an *envío* — removes the
translation step, aligns the navbar chip, dashboard stat card, pricing page,
and post-checkout confirmation around a single noun, and matches the singular
*envío* that already appears throughout the app
(`templates/dashboard/index.html:16,206`, `templates/dashboard/delete_account.html:10`,
`templates/home.html:99`).

This proposal is **UX-text-only**. No model field, URL, Stripe object, admin
class name, or test fixture is renamed.

## What Changes
- **Front-of-house templates** (anonymous + authenticated): every Spanish
  occurrence of the lemma *crédito* / *créditos* / *Créditos* in
  `templates/base.html`, `templates/home.html`, `templates/dashboard/index.html`,
  `templates/payments/packages.html`, `templates/payments/success.html` is
  replaced by *envío* / *envíos* / *Envíos* with grammar correction where the
  current sentence becomes tautological under the rename (specifically
  `home.html:66` "Cada crédito equivale a un envío" must be reworded; full
  rewrite shown in the dashboard/landing/pricing deltas).
- **Flash messages**: `apps/dashboard/views.py:150` (the only `messages.error`
  string mentioning créditos) is reworded to use *envíos*.
- **Admin model display**: `CreditPackage.Meta.verbose_name` /
  `verbose_name_plural` and `__str__` in `apps/payments/models.py:14-19` are
  updated. These render in the Django admin (a staff-visible UI surface) and
  qualify as "visible text" under the spirit of the request.
- **OpenSpec project glossary**: `openspec/project.md` Domain Context →
  *Credits* entry is rewritten to use *envíos* so future agents are not given
  the legacy term as ground truth.

### Out of scope (deliberate)
- **BREAKING-change avoidance**: no rename of `User.credits_remaining`,
  `CreditPackage` model class, `CreditPackage.credits` field,
  `StripePayment.credits_granted`, the `SIGNUP_BONUS_CREDITS` constant, the
  `/payments/paquetes/` URL, or any test/fixture name. Renaming any of these
  triggers a DB migration, breaks pending Stripe webhooks in flight, and
  requires lockstep changes in `apps/mailing/tasks.py` (the slow-drip
  decrement uses `F("credits_remaining") - 1`). These are internal identifiers
  with zero UX visibility and are excluded.
- **Documentation under `docs/`**: `docs/features/credits.md`,
  `docs/features/payments.md`, etc. are developer/operator docs, not user UI,
  and are out of scope. (A follow-up doc-only PR can sweep them after this
  ships.)

## Impact
- **Affected specs**:
  - `landing` — adds a terminology requirement covering the home page.
  - `dashboard` — adds a terminology requirement covering the navbar chip,
    the credit-card stat card heading, and the `toggle_campaign` flash message.
  - `pricing` (new capability) — codifies user-visible terminology on
    `/payments/paquetes/` and `/payments/exito/`, plus the admin-visible
    `CreditPackage` display.
- **Affected code**:
  - `templates/base.html:42`
  - `templates/home.html:65-66`
  - `templates/dashboard/index.html:41`
  - `templates/payments/packages.html:2,8,58`
  - `templates/payments/success.html:14`
  - `apps/dashboard/views.py:150`
  - `apps/payments/models.py:14-19`
  - `openspec/project.md` (Domain Context glossary line)
- **Pending-change coordination**: `add-mobile-responsive-layout` references
  the literal string `"Créditos disponibles"` in
  `openspec/changes/add-mobile-responsive-layout/specs/dashboard/spec.md:37`
  and the phrase "credits chip" in `specs/ui-shell/spec.md:9-11`. See
  `design.md` → *Sequencing with `add-mobile-responsive-layout`* for the
  resolution plan.
- **Risk**: trivial — no schema, URL, or webhook payload changes; pure copy
  edit. The two non-mechanical decisions (sentence rewording on `home.html:66`
  and `packages.html:8`) are spelled out in the deltas so reviewers can
  approve the exact final wording before implementation.
