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

### Requirement: Pricing page displays a platform-wide successful-sends trust signal
The pricing page `/payments/paquetes/` SHALL display the total count of
`MailingLog` records with `status = "sent"` as a visible trust signal inside
each package card and as a page-level footer line. The count MUST be injected
by the `packages` view as `successful_sends_count` and MUST NOT be hard-coded
in the template.

The trust signal MUST be hidden (not rendered) when `successful_sends_count` equals
zero, to avoid displaying a misleading "0 envíos exitosos" message on fresh
installations.

#### Scenario: Badge appears inside each card when sends exist
- **GIVEN** at least one `MailingLog` row with `status = "sent"` exists
- **WHEN** any user (authenticated or anonymous) requests `GET /payments/paquetes/`
- **THEN** each package card contains a green-colored element whose text
  matches the pattern `+{N} envíos exitosos en la plataforma`
  where `{N}` is the total count of `MailingLog(status="sent")` records
- **AND** the element appears immediately below the price line
  inside `<div class="mb-6">`

#### Scenario: Badge is hidden when no sends have been made
- **GIVEN** zero `MailingLog` rows exist (or all have `status = "failed"`)
- **WHEN** any user (authenticated or anonymous) requests `GET /payments/paquetes/`
- **THEN** the rendered HTML does NOT contain the substring
  `envíos exitosos en la plataforma`
- **AND** no element shows a count of `0`

#### Scenario: Footer trust bar appears below the Stripe disclaimer
- **GIVEN** at least one `MailingLog` row with `status = "sent"` exists
- **WHEN** the pricing page is rendered
- **THEN** the page contains a footer trust bar paragraph whose text
  matches the pattern
  `Más de {N} envíos completados por candidatos reales a través de FastJob`
  where `{N}` equals `successful_sends_count`
- **AND** the paragraph appears after the Stripe disclaimer paragraph

#### Scenario: Context variable reflects real-time database count
- **GIVEN** 42 `MailingLog` rows with `status = "sent"` and 10 with
  `status = "failed"`
- **WHEN** `GET /payments/paquetes/` is requested
- **THEN** the template context variable `successful_sends_count` equals `42`
- **AND** the rendered badge displays `42` (not `52` or any other value)

### Requirement: Spanish verbose names on StripePayment fields
All fields of `StripePayment` (`apps/payments/models.py`) SHALL declare
an explicit `verbose_name` in Spanish.

| Field | verbose_name |
|---|---|
| `user` | `"Usuario"` |
| `package` | `"Paquete"` |
| `stripe_session_id` | `"ID de sesión Stripe"` |
| `stripe_payment_intent` | `"Payment intent Stripe"` |
| `amount_eur` | `"Importe (€)"` |
| `credits_granted` | `"Envíos otorgados"` |
| `status` | `"Estado"` |
| `created_at` | `"Creado el"` |
| `completed_at` | `"Completado el"` |

`stripe_session_id` and `stripe_payment_intent` are internal Stripe
identifiers that must stay unique and searchable; only their displayed
labels are translated.

#### Scenario: StripePayment change form shows Spanish field labels
- **WHEN** a staff user opens `/admin/payments/stripepayment/<id>/change/`
- **THEN** each field label matches the Spanish string from the table above
- **AND** no English auto-generated label (e.g. "Stripe session id",
  "Credits granted", "Completed at") is visible

### Requirement: Spanish verbose name on SystemConfig field
`SystemConfig` (`apps/core/models.py`) SHALL declare `verbose_name="Guardar en carpeta Enviados"` on the `save_emails_to_sent_folder` field, and its `help_text` SHALL be entirely in Spanish with no English words embedded.

#### Scenario: SystemConfig change form shows Spanish label and help text
- **WHEN** a staff user opens `/admin/core/systemconfig/1/change/`
- **THEN** the field label reads `"Guardar en carpeta Enviados"`
- **AND** the help text contains no English words

### Requirement: Public pricing page access
The `/payments/paquetes/` view SHALL be accessible to any visitor, authenticated or anonymous. The `@login_required` decorator MUST be removed from `apps/payments/views.py:packages()`. All existing context variables (`packages`, `successful_sends_count`) MUST continue to be passed to the template unchanged.

#### Scenario: Anonymous visitor loads the pricing page
- **WHEN** an unauthenticated client sends `GET /payments/paquetes/`
- **THEN** the server responds with HTTP 200
- **AND** the response renders `templates/payments/packages.html` with the full package list
- **AND** the client is NOT redirected to `/accounts/login/`

#### Scenario: Authenticated user still loads the pricing page normally
- **GIVEN** a logged-in user
- **WHEN** they request `GET /payments/paquetes/`
- **THEN** the server responds with HTTP 200
- **AND** the page renders exactly as before this change

### Requirement: Anonymous purchase buttons redirect to login
When the requesting user is not authenticated, each package card's call-to-action SHALL render as an `<a>` link pointing to `/accounts/login/?next=/payments/paquetes/` instead of a POST form. The link MUST use the same visual styling as the primary-fill button used for authenticated users so the page appearance is consistent. The checkout `<form>` and `create_checkout` endpoint MUST only be reachable by authenticated users (the existing `@login_required` on `create_checkout` is preserved).

#### Scenario: Anonymous user sees login-redirect CTA
- **GIVEN** an unauthenticated client viewing `/payments/paquetes/`
- **WHEN** the page renders
- **THEN** each package card contains an `<a>` whose `href` is `/accounts/login/?next=/payments/paquetes/`
- **AND** no `<form>` with `action` pointing to `create_checkout` is present in the rendered HTML
- **AND** the `<a>` element carries the same Tailwind classes as the authenticated submit button

#### Scenario: Authenticated user still sees the checkout form
- **GIVEN** a logged-in user viewing `/payments/paquetes/`
- **WHEN** the page renders
- **THEN** each package card contains a `<form method="post">` with `action` pointing to `{% url 'create_checkout' package.pk %}`
- **AND** no login-redirect `<a>` with `?next=` is present in that form's place

### Requirement: Payments section root path redirects to packages listing
The payments URL namespace SHALL have an entry at the bare root path that redirects any client to the packages listing page, so that visiting `/payments/` never returns a 404.

The redirect MUST be non-permanent (HTTP 302) so that the target URL (`/payments/paquetes/`) can be changed in the future without browsers caching the old destination.

#### Scenario: Browser navigates directly to /payments/
- **WHEN** any client sends `GET /payments/`
- **THEN** the server MUST respond with HTTP 302
- **AND** the `Location` header MUST equal `/payments/paquetes/`

#### Scenario: Named URL payments_root resolves correctly
- **WHEN** `reverse("payments_root")` is called in Python code or a template tag
- **THEN** it MUST resolve to `/payments/`

#### Scenario: Existing payment_packages URL is unaffected
- **WHEN** `reverse("payment_packages")` is called
- **THEN** it MUST still resolve to `/payments/paquetes/` (unchanged by this addition)

