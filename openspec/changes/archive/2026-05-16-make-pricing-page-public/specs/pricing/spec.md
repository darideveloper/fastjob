## ADDED Requirements

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

## MODIFIED Requirements

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
