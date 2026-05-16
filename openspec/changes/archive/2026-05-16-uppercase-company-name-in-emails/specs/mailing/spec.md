## ADDED Requirements

### Requirement: Company Name Rendered in Uppercase
`EmailTemplate.render()` SHALL uppercase the `company_name` argument before substituting it into `{company_name}` placeholders in both the subject and the HTML body, so every outgoing CV-campaign email displays the company name in all-caps regardless of the casing stored in the database.

The transformation MUST be applied in the Python render layer — not inside stored template markup — so that templates remain plain and no database migration is required.

#### Scenario: Mixed-case company name is uppercased in subject
- **GIVEN** an `EmailTemplate` whose subject is `"Solicitud para {company_name}"`
- **WHEN** `render(company_name="Acme Corp", unsubscribe_url="http://u")` is called
- **THEN** the returned subject is `"Solicitud para ACME CORP"`

#### Scenario: Mixed-case company name is uppercased in HTML body
- **GIVEN** an `EmailTemplate` whose body contains `"<p>Estimados {company_name},</p>"`
- **WHEN** `render(company_name="Acme Corp", unsubscribe_url="http://u")` is called
- **THEN** the returned body is `"<p>Estimados ACME CORP,</p>"`

#### Scenario: Already-uppercase company name is unaffected
- **GIVEN** a company name already stored as `"TECHCO S.L."`
- **WHEN** `render()` is called
- **THEN** the rendered value is `"TECHCO S.L."` — idempotent, no double-transformation

#### Scenario: Lowercase company name is fully uppercased
- **GIVEN** a company name stored as `"startup labs"`
- **WHEN** `render()` is called
- **THEN** the rendered value is `"STARTUP LABS"`
