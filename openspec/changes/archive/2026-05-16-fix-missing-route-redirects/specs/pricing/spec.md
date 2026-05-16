## ADDED Requirements

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
