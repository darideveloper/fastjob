# pricing Specification Delta

## ADDED Requirements

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
- **WHEN** any authenticated user requests `GET /payments/paquetes/`
- **THEN** each package card contains a green-colored element whose text
  matches the pattern `+{N} envíos exitosos en la plataforma`
  where `{N}` is the total count of `MailingLog(status="sent")` records
- **AND** the element appears immediately below the price line
  inside `<div class="mb-6">`

#### Scenario: Badge is hidden when no sends have been made
- **GIVEN** zero `MailingLog` rows exist (or all have `status = "failed"`)
- **WHEN** any authenticated user requests `GET /payments/paquetes/`
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
