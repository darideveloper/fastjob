## Context
FastJob sells what users perceive as "send a CV to a company". Internally
that unit is stored as `User.credits_remaining` (an integer counter
decremented by `apps/mailing/tasks.py:86` and incremented by the Stripe
webhook in `apps/payments/views.py:147`). The user-facing copy currently
calls it a *crédito* — even though the same templates refer to the action
as an *envío* in adjacent sentences (e.g.
`templates/dashboard/index.html:206` "{{ paginator.count }} envíos" sits
just below `:41` "Créditos disponibles"). The rename consolidates around
the term users already see in half the UI.

Stakeholders: end users (Spanish-speaking job seekers), staff using the
Django admin (the `Paquete de Créditos` verbose name), and future AI
agents reading `openspec/project.md`.

## Goals / Non-Goals
- **Goals**
  - Every Spanish-language *user-visible* occurrence of `crédito[s]`
    (any case) renders as `envío[s]` after this change.
  - Sentences that become tautological under a literal substitution
    (`home.html:66`, `packages.html:8`) are reworded so the final copy
    still reads naturally.
  - The Django admin's `CreditPackage` listing — visible to staff and
    therefore in scope under "all visible texts" — uses the new noun.
  - `openspec/project.md` Domain Context entry is updated so future
    proposals don't reintroduce the legacy term.
- **Non-Goals**
  - Renaming database columns or Python identifiers
    (`credits_remaining`, `credits_granted`, `credits`, `CreditPackage`,
    `SIGNUP_BONUS_CREDITS`).
  - Changing the URL `/payments/paquetes/` (the URL slug "paquetes"
    means "packages", not "créditos", so it is unaffected by the
    request).
  - Translating `docs/features/credits.md` or any other developer
    documentation under `docs/`.
  - Any change to Stripe product names, webhook payload shapes, or
    receipt copy (those are configured in the Stripe dashboard, not in
    this codebase).

## Decisions

### Decision: Keep internal field/class names unchanged
**What:** Templates render `{{ user.credits_remaining }} envíos` and
`{{ payment.credits_granted }} envíos` — i.e. the *number* still comes
from a Python attribute called `credits_*`, and only the noun next to
the number changes.
**Why:** Renaming the model field forces a DB migration on a column
read by the slow-drip Celery worker (`apps/mailing/tasks.py:36,86`) and
written transactionally by the Stripe webhook handler
(`apps/payments/views.py:147`). The proposal's request is "visible
texts", not a refactor; coupling them would multiply scope and risk.
**Alternatives considered:**
1. Full rename to `sends_remaining` / `EnvioPackage` — rejected:
   migration, webhook idempotency surface, test fixture churn,
   coordination with `add-mobile-responsive-layout`.
2. Add a `@property def envios_remaining(self): return self.credits_remaining`
   alias — rejected as gratuitous indirection; the template-side `|`
   noun *is the rename*, no Python alias needed.

### Decision: Update `CreditPackage` admin verbose names and `__str__`
**What:** `Meta.verbose_name = "Paquete de Envíos"`,
`verbose_name_plural = "Paquetes de Envíos"`, and `__str__` returns
`f"{self.name} — {self.credits} envíos por {self.price_eur}€"`.
**Why:** These strings render in the Django admin (the changelist
header, the breadcrumb, the object dropdowns referenced from
`StripePayment.package`). The user said "all visible texts"; admin is
visible to staff. The class name `CreditPackage` and field `credits`
stay — only display strings change, so no migration.
**Alternatives considered:** Skipping admin (out of "visible" depending
on definition) — rejected because the user wrote "or similar" and the
admin verbose names are user-visible Spanish copy in exactly the same
way template strings are.

### Decision: Reword two tautology-creating sentences
**What:**
- `templates/home.html:66` — current: *"Cada crédito equivale a un
  envío. Elige el paquete que mejor se adapte a ti."* → new:
  *"Cada envío manda tu CV a una empresa. Elige el paquete que mejor
  se adapte a ti."*
- `templates/payments/packages.html:8` — current: *"Cada crédito = un
  CV enviado. Sin suscripciones, sin sorpresas."* → new: *"Cada envío
  = un CV a una empresa. Sin suscripciones, sin sorpresas."*
**Why:** A literal substitution would produce *"Cada envío equivale a
un envío"*, which is meaningless. Both rewrites preserve the original
copywriting intent (one unit = one CV to one company; no recurring
billing) without re-introducing the *crédito* term.
**Alternatives considered:** Drop the sentence entirely on
`packages.html:8` — rejected because the "no subscriptions" reassurance
on the pricing page is load-bearing for conversion.

### Decision: New `pricing` capability vs. extending `landing`/`dashboard`
**What:** Introduce a new `pricing` capability that owns user-visible
behavior on `/payments/paquetes/` and `/payments/exito/`, plus the
`CreditPackage` admin display. Add per-template terminology
requirements to `landing` and `dashboard` for their own pages.
**Why:** No `pricing` (or `payments-ui`) capability exists in
`openspec/specs/` today, but the pricing page's behavior — what it
shows, what it links to, how it labels its packages — is exactly the
sort of thing a capability is supposed to codify. Better to introduce
the capability with a single small terminology requirement than to
overload `landing` with pricing-page rules. `landing` and `dashboard`
already exist and are the natural homes for their own pages.

## Risks / Trade-offs
- **Sequencing risk with `add-mobile-responsive-layout`** — that
  proposal cites `"Créditos disponibles"` as the literal text inside a
  scenario. If this change ships first, the mobile-responsive scenario
  becomes inaccurate the moment its tasks run. Mitigation: see
  *Migration Plan* below.
- **Stale screenshots / external blog posts** — no inventory of
  external assets exists; if any marketing screenshot uses the legacy
  term it stays stale until manually replaced. Out of scope here;
  flagged for the marketing owner.
- **Stripe receipts** — Stripe sends users a receipt with the
  *product name* configured in the Stripe dashboard. If the product is
  named "Crédito" there, the receipt will still say so. Action:
  product owner updates Stripe dashboard product names manually after
  this ships. (Not codifiable in a spec.)

## Migration Plan
1. **Sequencing with `add-mobile-responsive-layout`**: that change is
   currently `0/23 tasks` (per `openspec list`), i.e. *unimplemented*.
   The cleanest resolution is to **land this terminology proposal
   first**, then update the affected scenarios in
   `add-mobile-responsive-layout` (the dashboard delta line 37 and
   `ui-shell` delta lines 9-11) to use the new wording before
   implementation begins. Concretely: a single follow-up commit on the
   `add-mobile-responsive-layout` branch swaps "Créditos disponibles"
   → "Envíos disponibles" and "credits chip" → "envíos chip" in its
   spec deltas. No code conflict because that proposal hasn't written
   any code yet.
2. **No DB migration** — zero schema change.
3. **No data backfill** — `credits_remaining` integers are unchanged.
4. **Rollback** — pure text edit. If a stakeholder rejects the new
   wording post-merge, a single PR reverts the templates / models.py /
   views.py / project.md hunks. No state is at risk.

## Open Questions
- Should the URL `/payments/paquetes/` also become `/payments/envios/`?
  **Recommendation: no**, because *paquetes* is a different word
  ("packages") and the user's request was about *créditos*; including
  it expands scope and risks breaking external links / bookmarks /
  Google indexing. Calling it out so reviewers can override.
- Should `apps/accounts/signals.py:13` `SIGNUP_BONUS_CREDITS` be
  renamed for code-side consistency? **Recommendation: no, in this
  proposal** — internal identifier, zero UX visibility, would belong
  in a separate refactor ticket.
- Does the Stripe dashboard need a parallel terminology update on the
  Product name? **Recommendation: yes, but manual** — flagged in
  *Risks* above; not a code change.
