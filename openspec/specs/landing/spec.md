# landing Specification

## Purpose
TBD - created by archiving change add-company-filter-finder. Update Purpose after archive.
## Requirements
### Requirement: Public Company-Finder Section on Landing Page
The public landing page SHALL include a section, positioned above the call-to-action that links to the pricing/packages page, that lets anonymous visitors explore the company database by sector and location. The section MUST be 100% functional without authentication. It MUST consist of two searchable dropdown widgets (sector and location) and a live counter showing the number of matching companies. The widgets' option lists MUST be sourced from the same allowed-options whitelist as the dashboard. The counter MUST display only an integer and MUST NOT expose any company name, email, primary key, or other row-level data anywhere in the rendered HTML or JavaScript.

#### Scenario: Anonymous visitor sees the section without logging in
- **GIVEN** a visitor with no authenticated session
- **WHEN** they load the landing page
- **THEN** the company-finder section is rendered with both dropdowns populated and a placeholder counter

#### Scenario: Dropdown options match the current database
- **GIVEN** the `Company` table contains the distinct non-empty areas `{"Tecnología", "Diseño"}`
- **WHEN** an anonymous visitor opens the area dropdown on the landing page
- **THEN** the dropdown lists exactly those two values (alphabetically sorted)
- **AND** the visitor cannot enter a value not in the list and have it accepted

#### Scenario: Counter updates when filters change
- **GIVEN** the visitor has selected `area="Tecnología"` and `location=""`
- **WHEN** the visitor selects `location="Madrid"` from the second dropdown
- **THEN** the counter re-fetches from the public count endpoint
- **AND** the displayed integer reflects the new combined filter

#### Scenario: Section never exposes company-identifying data
- **WHEN** the landing page is rendered with any combination of filter selections
- **THEN** the rendered HTML and the JSON responses fetched by the section's JavaScript contain only label strings (the option lists) and an integer count
- **AND** no company email, name, primary key, or row-level field appears in any DOM node or network response

#### Scenario: Section drives traffic to the pricing page
- **GIVEN** the visitor has used the finder and seen a non-zero count
- **WHEN** they click the section's "Ver paquetes" call-to-action
- **THEN** they navigate to `/payments/paquetes/` (the pricing page)

#### Scenario: Per-IP rate limit applies the same as the dashboard
- **WHEN** a single client IP exceeds the configured per-hour threshold on the public count endpoint
- **THEN** subsequent counter updates from that IP receive `429 Too Many Requests`
- **AND** the landing-page UI degrades gracefully (counter shows a dash or last-known value rather than crashing)

### Requirement: Hero CTAs fit on a single line at 320 px
The two hero call-to-action buttons in `templates/home.html` ("Empezar con Google" and "Empezar con Microsoft") SHALL each render on a single line at viewport 320 px without wrapping their label. Below the `sm` breakpoint, padding and font size MUST be reduced (e.g. `px-6 py-3 text-base`); at `sm` and above, padding and font size MUST match today's desktop look (`px-8 py-4 text-lg`).

#### Scenario: Both hero CTAs render on one line at 320 px
- **GIVEN** an anonymous visitor at viewport 320 × 568
- **WHEN** the home page (`/`) is rendered
- **THEN** the "Empezar con Google" button's label "Empezar con Google" occupies exactly one line within the button
- **AND** the "Empezar con Microsoft" button's label occupies exactly one line within the button

#### Scenario: Hero CTAs at 768 px and 1440 px match today's look
- **GIVEN** an anonymous visitor at viewport 768 × 1024 or 1440 × 900
- **WHEN** the home page is rendered
- **THEN** the buttons render with the original `px-8 py-4 text-lg` paddings and font size
- **AND** both buttons sit on the same horizontal row (per the existing `flex flex-col sm:flex-row` parent)

### Requirement: Company-finder CTA fits on a single line at 320 px
The "Ver paquetes y empezar" CTA below the public company-finder section in `templates/home.html` SHALL render on a single line at viewport 320 px, with its trailing arrow icon on the same line as the label. The same responsive scaling pattern as the hero CTAs MUST apply: smaller padding and font below `sm`, original size at `sm` and above.

#### Scenario: Company-finder CTA renders on one line at 320 px
- **GIVEN** an anonymous visitor at viewport 320 × 800
- **WHEN** they scroll to the company-finder section on the home page
- **THEN** the "Ver paquetes y empezar" CTA's label and its trailing arrow are on the same single line within the button
- **AND** clicking it navigates to `/payments/paquetes/` (preserving the existing target from the `add-company-filter-finder` change)

#### Scenario: Company-finder CTA at desktop matches today's look
- **GIVEN** an anonymous visitor at viewport 1024 × 768
- **WHEN** the home page is rendered
- **THEN** the CTA renders with `px-8 py-4 text-lg` exactly as it does today

### Requirement: Landing page uses "envíos" terminology for the per-CV unit
The public landing page (`templates/home.html`) SHALL refer to the
purchasable unit-of-value as `envío` / `envíos` (singular / plural,
matching Spanish grammar) in every user-visible string. The legacy term
`crédito` / `créditos` MUST NOT appear anywhere in the rendered HTML of
the landing page (including, but not limited to: section headings,
taglines, button labels, and the "How it works" step list). When a
sentence relies on the contrast between the two terms (e.g. the current
"Cada crédito equivale a un envío"), it MUST be reworded so it remains
meaningful under the new vocabulary rather than becoming tautological.

#### Scenario: Landing page rendered to an anonymous visitor contains no "crédito" text
- **GIVEN** a visitor with no authenticated session
- **WHEN** they request `GET /` and the response body is rendered
- **THEN** a case-insensitive regex search of the rendered HTML for
  `cr[ée]dito` returns zero matches
- **AND** the "How it works" step labelled `3.` reads `3. Compra envíos`
  (not `3. Compra créditos`)

#### Scenario: The reworded tagline reads naturally
- **WHEN** the landing page renders the tagline immediately below the
  `3. Compra envíos` heading
- **THEN** the tagline text is
  `Cada envío manda tu CV a una empresa. Elige el paquete que mejor se adapte a ti.`
- **AND** the rendered sentence does NOT contain the substring
  `equivale a un envío` (the previous tautology-prone phrasing)

#### Scenario: Pre-existing "envío" usage on the landing page is preserved
- **GIVEN** the existing copy at `templates/home.html` line ~99
  ("Asunto y cuerpo aleatorios en cada envío…")
- **WHEN** the landing page renders after the change
- **THEN** that sentence is unchanged
- **AND** the noun "envío" is used consistently across both the
  pricing-step copy and the deliverability copy

