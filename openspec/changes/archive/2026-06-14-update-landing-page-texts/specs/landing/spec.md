## MODIFIED Requirements

### Requirement: Landing page reflects the CV-attachment delivery model
The public landing page (`templates/home.html`) SHALL describe the product as sending the CV **as a PDF attachment**, not as a download link. The strings `enlace de descarga`, `enlaces de descarga`, and `Sin adjuntos` MUST NOT appear in the rendered HTML of `/` after this change. The replacement copy MUST stay accurate to the delivery flow established by `apps/mailing/migrations/0008_auto_20260514_0522.py` (the CV ships as a PDF attached to the outbound email).

#### Scenario: Hero subtitle describes attachment delivery, not link delivery
- **GIVEN** an anonymous visitor at any viewport
- **WHEN** they request `GET /` and the response body is rendered
- **THEN** the hero subtitle paragraph contains the substring `PDF` (or `adjunto`) and describes email sending from Gmail/Outlook
- **AND** a case-insensitive regex search of the rendered HTML for `enlaces? de descarga` returns zero matches

#### Scenario: Trust-signal card no longer claims "Sin adjuntos"
- **WHEN** the landing page renders the deliverability trust-signal grid
- **THEN** no card on that grid contains the heading `Sin adjuntos`
- **AND** the card that previously carried that heading now describes the PDF-attachment behavior in a positive frame (e.g. `CV en PDF adjunto`)

### Requirement: Landing page uses "envíos" terminology for the per-CV unit
The public landing page (`templates/home.html`) SHALL refer to the purchasable unit-of-value as `envío` / `envíos` (singular / plural, matching Spanish grammar) in every user-visible string. The legacy term `crédito` / `créditos` MUST NOT appear anywhere in the rendered HTML of the landing page (including, but not limited to: section headings, taglines, button labels, and the "How it works" step list). The landing page SHALL also avoid the strings `enlace de descarga` / `enlaces de descarga` (see also the new `Landing page reflects the CV-attachment delivery model` requirement above): the product now ships the CV as a PDF attachment, so any link-based phrasing is factually wrong. When a sentence relies on the contrast between the two terms (e.g. the current "Cada crédito equivale a un envío"), it MUST be reworded so it remains meaningful under the new vocabulary rather than becoming tautological.

#### Scenario: Landing page rendered to an anonymous visitor contains no "crédito" text
- **GIVEN** a visitor with no authenticated session
- **WHEN** they request `GET /` and the response body is rendered
- **THEN** a case-insensitive regex search of the rendered HTML for `cr[ée]dito` returns zero matches
- **AND** the "How it works" step labelled `3.` reads `3. Compra envíos` (not `3. Compra créditos`)

#### Scenario: The reworded tagline reads naturally
- **WHEN** the tagline renders immediately below the `3. Compra envíos` heading
- **THEN** the tagline text is `Cada envío manda tu CV a una empresa. Elige el paquete que mejor se adapte a ti.`
- **AND** the rendered sentence does NOT contain the substring `equivale a un envío` (the previous tautology-prone phrasing)

#### Scenario: Pre-existing "envío" usage on the landing page is preserved
- **GIVEN** the existing copy at `templates/home.html` ("Cada candidatura utiliza asuntos y textos adaptados para que el contacto con las empresas sea más profesional y cercano.")
- **WHEN** the landing page renders after the change
- **THEN** that sentence is present
- **AND** the noun "envío" is used consistently across both the pricing-step copy and the deliverability copy
