## ADDED Requirements

### Requirement: Dashboard surfaces use "envíos" terminology
The authenticated dashboard surface SHALL use the noun `envío` / `envíos`
(singular / plural) in every user-visible string — including the global
navbar chip in `templates/base.html`, the stat-card heading in
`templates/dashboard/index.html`, and any flash message emitted by
`apps/dashboard/views.py` — and MUST NOT render the literal substring
`crédito` / `créditos` (any case, with or without the acute accent) in
the dashboard's HTML or in queued messages-framework text. The numeric
value displayed next to the noun MUST continue to be sourced from
`User.credits_remaining`; the underlying field is intentionally NOT
renamed, only the noun rendered next to its value changes.

#### Scenario: Authenticated navbar chip shows "envíos"
- **GIVEN** an authenticated user with `credits_remaining = 7`
- **WHEN** any page extending `base.html` is rendered for that user
- **THEN** the navbar chip renders the text `7 envíos`
- **AND** the chip does NOT contain the substring `créditos`

#### Scenario: Dashboard stat card heading is "Envíos disponibles"
- **GIVEN** an authenticated user opens `GET /dashboard/`
- **WHEN** the stat-card row at the top of the dashboard is rendered
- **THEN** the card label above the integer reads `Envíos disponibles`
- **AND** the rendered HTML contains no occurrence of the regex
  `[Cc]r[ée]dito`

#### Scenario: "No credits" flash message uses "envíos"
- **GIVEN** an authenticated user with `credits_remaining = 0`, a
  linked OAuth provider, and an active CV
- **WHEN** the user submits `POST /dashboard/toggle-campaign/` with
  `action=start`
- **THEN** a Django messages-framework `error` is queued whose body is
  `"No tienes envíos disponibles. Compra un paquete para continuar."`
- **AND** no other queued message text references the word "crédito"

#### Scenario: Internal field name is intentionally preserved
- **GIVEN** the model field `User.credits_remaining` (defined at
  `apps/accounts/models.py:11`)
- **WHEN** any dashboard template renders the user's balance
- **THEN** the template still reads the value via
  `{{ user.credits_remaining }}`
- **AND** no DB migration is generated for this change (the rename is
  purely textual; the integer column keeps its identifier)
