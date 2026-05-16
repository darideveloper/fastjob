# pricing Specification

## Purpose
TBD - created by archiving change rename-credits-to-envios. Update Purpose after archive.
## Requirements
### Requirement: Pricing page uses "envíos" terminology end-to-end
The pricing page `/payments/paquetes/` SHALL refer to the purchasable
unit as `envío` / `envíos` in every visible string rendered by
`templates/payments/packages.html` — including the `<title>`, the
page subtitle, each per-card feature list, and each per-card purchase
button. The URL slug `paquetes/` is intentionally NOT renamed; only
the human-readable copy is in scope.

#### Scenario: Pricing page `<title>` uses "Envíos"
- **WHEN** any client requests `GET /payments/paquetes/`
- **THEN** the `<title>` element of the response reads
  `Paquetes de Envíos — FastJob`
- **AND** the title does NOT contain the substring `Créditos`

#### Scenario: Subtitle reads naturally without re-introducing "crédito"
- **WHEN** the pricing page is rendered
- **THEN** the subtitle text immediately under the `<h1>` reads
  `Cada envío = un CV a una empresa. Sin suscripciones, sin sorpresas.`
- **AND** the rendered subtitle does NOT contain the substring
  `crédito`

#### Scenario: Purchase button shows "envíos"
- **GIVEN** an active `CreditPackage` row whose `credits = 200`
  exists in the database
- **WHEN** the pricing page is rendered for any client
- **THEN** that package's purchase button reads `Comprar 200 envíos`
- **AND** no purchase button on the page contains the substring
  `créditos`

#### Scenario: URL slug "/paquetes/" is preserved
- **WHEN** the routing table is inspected
- **THEN** the named URL `payment_packages` continues to resolve to
  the path `/payments/paquetes/`
- **AND** no redirect from `/payments/envios/` is added (out of scope
  per `proposal.md` → "Out of scope")

### Requirement: Post-checkout success page reports the grant in "envíos"
The post-checkout success page SHALL report the granted quantity using
the noun `envíos` in every visible string rendered by
`templates/payments/success.html` (route `/payments/exito/`). The value
itself MUST continue to be read from `payment.credits_granted`; the
model field on `StripePayment` is intentionally NOT renamed, only the
noun rendered next to it changes.

#### Scenario: Success page shows "X envíos"
- **GIVEN** a `StripePayment` with `credits_granted = 50` and
  `status = "completed"` linked to the current session
- **WHEN** the user lands on `GET /payments/exito/?session_id=...`
- **THEN** the rendered HTML contains the substring
  `Se han añadido <strong class="text-brand">50 envíos</strong> a tu cuenta.`
- **AND** the rendered HTML contains no occurrence of the regex
  `[Cc]r[ée]dito`

### Requirement: CreditPackage admin display uses "Envíos"
The `CreditPackage` model (`apps/payments/models.py`) SHALL declare
admin-facing display strings using the term `Envíos`. Specifically:
`Meta.verbose_name` reads `"Paquete de Envíos"`,
`Meta.verbose_name_plural` reads `"Paquetes de Envíos"`, and the
`__str__` return value uses `envíos` (e.g.
`"Starter — 50 envíos por 9.99€"`). The Python class name
`CreditPackage`, the integer field `credits`, and the
`stripe_price_id` field are intentionally NOT renamed — they are
internal identifiers with zero end-user visibility.

#### Scenario: Admin changelist header reads "Paquetes de Envíos"
- **GIVEN** a Django staff user with permission to view `payments`
- **WHEN** they open the admin URL
  `/admin/payments/creditpackage/`
- **THEN** the page heading rendered by Django admin reads
  `Paquetes de Envíos`
- **AND** breadcrumbs and the "add" button refer to the singular
  form `Paquete de Envíos`

#### Scenario: `CreditPackage.__str__` uses "envíos"
- **GIVEN** a `CreditPackage` instance with
  `name="Starter"`, `credits=50`, `price_eur=Decimal("9.99")`
- **WHEN** `str(instance)` is evaluated (used by the
  `StripePayment.package` foreign-key dropdown and the changelist)
- **THEN** the returned string equals `"Starter — 50 envíos por 9.99€"`
- **AND** the returned string does NOT contain the substring
  `créditos`

#### Scenario: No DB migration alters table or column identifiers
- **WHEN** `python manage.py makemigrations payments` is run after
  the change
- **THEN** any generated migration contains only `Meta` option edits
  (`verbose_name`, `verbose_name_plural`)
- **AND** no `RenameField`, `RenameModel`, or `AlterField` operation
  is generated against `CreditPackage` or `StripePayment`

### Requirement: Negative Balance Forgiveness on Purchase
When a user with a negative credit balance (due to the hidden multiplier margin) purchases a new credit package, the system MUST "forgive" the debt so that their final balance matches the purchased quantity.
- The amount added to `credits_remaining` MUST be `package.credits + abs(min(0, user.credits_remaining))`.

#### Scenario: User at -5 credits buys 50
- **GIVEN** a user with `credits_remaining = -5`.
- **WHEN** they complete a purchase for a package with 50 credits.
- **THEN** the system MUST add 55 credits to their balance.
- **AND** the final `credits_remaining` MUST be `50`.

### Requirement: Tiered pricing card visual hierarchy
`templates/payments/packages.html` SHALL render its package options in a responsive card grid using `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6`. Every card SHALL use the shared card chrome (`bg-white border border-brand-muted rounded-2xl shadow-sm p-6 sm:p-8`). One card MAY be marked as "recommended" via a ribbon using `bg-brand-dark text-white` and a slightly elevated shadow (`shadow-lg`) — when present, the ribbon MUST contain exactly the Spanish label `Recomendado`. The price per card uses the `text-display` typographic token in `brand.dark`; the unit label uses `text-caption text-brand-ink/70`. Each card's CTA uses the primary-fill button variant. No view-context, pricing, or routing change is introduced — purely visual.

#### Scenario: Pricing grid is responsive across breakpoints
- **WHEN** the packages page is rendered at viewports 320, 640, and 1024 px
- **THEN** the cards are laid out in 1, 2, and 3 columns respectively
- **AND** no card overflows horizontally at 320 px
- **AND** every card retains the same card chrome (`rounded-2xl`, `border-brand-muted`)

#### Scenario: Recommended tier is visually distinct
- **GIVEN** a package the view marks as recommended
- **WHEN** the page renders
- **THEN** that card displays a ribbon with `bg-brand-dark text-white` containing the label `Recomendado`
- **AND** the card's shadow is `shadow-lg` (vs `shadow-sm` on the other cards)
- **AND** the per-card CTA still uses primary-fill

### Requirement: Payment success page hero
`templates/payments/success.html` SHALL render a centered hero card on a subtle gradient backdrop (`bg-gradient-to-br from-brand-cyan/15 via-white to-brand/10`). The user's new envíos balance SHALL be the visual hero, rendered with the `text-display` token in `brand.dark`. The existing CTA label `Ir al Panel de Control` (`success.html:19`) MUST be preserved — it MUST NOT be shortened to `Ir al panel` or otherwise re-translated; it SHALL continue to link to `/dashboard/`.

#### Scenario: Success page surfaces the new balance prominently
- **GIVEN** a user who just completed a Stripe checkout
- **WHEN** they land on `/payments/success/`
- **THEN** the new envíos balance renders with the `text-display` size token
- **AND** the color resolves to `brand.dark` (`#003D99`)
- **AND** a single primary-fill CTA labelled exactly `Ir al Panel de Control` points to `/dashboard/`

