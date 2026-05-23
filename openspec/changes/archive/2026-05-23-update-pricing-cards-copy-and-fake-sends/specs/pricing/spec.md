## MODIFIED Requirements

### Requirement: Pricing page uses "envíos" terminology end-to-end
The pricing page `/payments/paquetes/` SHALL refer to the purchasable
unit as `envío` / `envíos` in every visible string rendered by
`templates/payments/packages.html` — including the `<title>`, the
page subtitle, each per-card feature list, and each per-card purchase
button. The URL slug `paquetes/` is intentionally NOT renamed; only
the human-readable copy is in scope.

The per-card feature-list item that displays the credits count MUST
read `CVs enviados exitosamente` (NOT the previous `CVs enviados`).
The `<strong>` number and the label text MUST be wrapped together in a
`<span>` so they form a single flex item within the `flex gap-2` list,
preventing the gap utility from inserting excess space between the
number and the label.

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

#### Scenario: Feature list reads "CVs enviados exitosamente" with correct spacing
- **GIVEN** an active `CreditPackage` with `credits = 50`
- **WHEN** the pricing page is rendered
- **THEN** the per-card feature list item renders as
  `<span><strong>50</strong> CVs enviados exitosamente</span>`
- **AND** the `<strong>` and the label text are siblings inside a single `<span>`,
  NOT separate flex items
- **AND** the rendered HTML does NOT contain the substring `CVs enviados`
  without the word `exitosamente` immediately following it

#### Scenario: URL slug "/paquetes/" is preserved
- **WHEN** the routing table is inspected
- **THEN** the named URL `payment_packages` continues to resolve to
  the path `/payments/paquetes/`
- **AND** no redirect from `/payments/envios/` is added (out of scope
  per `proposal.md` → "Out of scope")

### Requirement: Pricing page displays a platform-wide successful-sends trust signal
The pricing page `/payments/paquetes/` SHALL display the total count of
`MailingLog` records with `status = "sent"` as a visible trust signal in a
**page-level footer bar only**. No per-card badge is rendered inside individual
package cards. The count MUST be injected by the `packages` view as
`successful_sends_count` and MUST NOT be hard-coded in the template.

The `packages` view MUST compute `successful_sends_count` as:
```
max(real_count, SystemSettings.get().displayed_sends_floor)
```
where `real_count` is `MailingLog.objects.filter(status=MailingLog.Status.SENT).count()`
and `displayed_sends_floor` is the configured floor value from `SystemSettings`
(default `0`). When `displayed_sends_floor` is `0` and `real_count` is `0`,
the computed value is `0` and the trust signal MUST be hidden.

The trust signal MUST be hidden (not rendered) when the computed `successful_sends_count`
equals zero, to avoid displaying a misleading "0 envíos exitosos" message.

#### Scenario: Footer trust bar shows floor value when real count is below floor
- **GIVEN** `SystemSettings.displayed_sends_floor = 500`
- **AND** only 12 `MailingLog` rows with `status = "sent"` exist
- **WHEN** any user requests `GET /payments/paquetes/`
- **THEN** the footer trust bar displays `500` (the floor value, not `12`)
- **AND** the page contains a paragraph matching
  `Más de 500 envíos completados por candidatos reales a través de FastJob`

#### Scenario: Footer trust bar shows real count when it exceeds the floor
- **GIVEN** `SystemSettings.displayed_sends_floor = 100`
- **AND** 842 `MailingLog` rows with `status = "sent"` exist
- **WHEN** any user requests `GET /payments/paquetes/`
- **THEN** the footer trust bar displays `842`
- **AND** the page contains a paragraph matching
  `Más de 842 envíos completados por candidatos reales a través de FastJob`

#### Scenario: No per-card badge is rendered
- **GIVEN** the computed `successful_sends_count` is greater than zero
- **WHEN** any user (authenticated or anonymous) requests `GET /payments/paquetes/`
- **THEN** the rendered HTML does NOT contain the substring
  `envíos exitosos en la plataforma` inside any card's `<div class="mb-6">`
- **AND** the substring appears only once, in the footer paragraph

#### Scenario: Footer trust bar is hidden when computed count is zero
- **GIVEN** `SystemSettings.displayed_sends_floor = 0`
- **AND** zero `MailingLog` rows with `status = "sent"` exist
- **WHEN** any user (authenticated or anonymous) requests `GET /payments/paquetes/`
- **THEN** the rendered HTML does NOT contain the substring
  `envíos completados por candidatos reales`
- **AND** no element shows a count of `0`

#### Scenario: Footer trust bar appears below the Stripe disclaimer
- **GIVEN** the computed `successful_sends_count` is greater than zero
- **WHEN** the pricing page is rendered
- **THEN** the page contains a footer trust bar paragraph whose text
  matches the pattern
  `Más de {N} envíos completados por candidatos reales a través de FastJob`
  where `{N}` equals the computed `successful_sends_count`
- **AND** the paragraph appears after the Stripe disclaimer paragraph
