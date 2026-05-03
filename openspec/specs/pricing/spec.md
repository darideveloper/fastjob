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

