# landing Specification

## Purpose
TBD - created by archiving change add-company-filter-finder. Update Purpose after archive.
## Requirements
### Requirement: Public Company-Finder Section on Landing Page

The public landing page SHALL include a section, positioned above the call-to-action that links to the pricing/packages page, that lets anonymous visitors explore the company database by sector and location. The section MUST be 100% functional without authentication. It MUST consist of two searchable dropdown widgets (sector and location) and a live counter showing the number of matching companies. The widgets' option lists MUST be sourced from the same allowed-options whitelist as the dashboard. The counter MUST display only an integer and MUST NOT expose any company name, email, primary key, or other row-level data anywhere in the rendered HTML or JavaScript.

When the section's backing API requests fail (rate limit `429`, server error, or network failure), the section MUST degrade gracefully and visibly: it MUST NOT silently render empty, non-functional dropdowns. The visitor MUST be shown a recoverable error state with a retry affordance.

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

- **WHEN** a single real client IP exceeds the configured per-hour threshold on the public count endpoint
- **THEN** subsequent counter updates from that IP receive `429 Too Many Requests`
- **AND** the counter degrades gracefully (shows a dash or last-known value rather than crashing)
- **AND** other visitors behind the same reverse proxy are unaffected, because the limit is keyed on the resolved real client IP

#### Scenario: Option-list failure shows a recoverable error instead of empty dropdowns

- **GIVEN** the `GET /api/companies/filter-options/` request fails (e.g. `429` or a server error)
- **WHEN** the landing-page company-finder section initialises
- **THEN** the section displays a visible error message with a retry control
- **AND** it does NOT render silently empty, non-functional dropdowns
- **AND** activating the retry control re-fetches the options and, on success, renders the populated widgets

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

### Requirement: Landing hero adopts the new brand palette while preserving its immersive treatment
The hero `<section>` of `templates/home.html` SHALL keep its existing **dark-immersive** treatment (a brand-colored gradient backdrop with white body text). The gradient stops MUST be updated from the current `from-brand to-brand-dark` to `from-brand via-brand-dark to-brand-cyan/40` so the hero now reads as Vibrant Blue → Deep Cobalt with an Electric Cyan glow accent on the bottom-right. The headline MUST use the `text-display` typographic token (or its breakpoint-stepped fallback) in `text-white`. The subtitle MUST use `text-brand-cloud` — never `text-brand-muted` (which is a transparent tint suitable only for backgrounds) and never `text-brand-cyan` (insufficient contrast against the Cobalt midpoint).

The two OAuth CTAs MUST preserve their existing visual hierarchy: "Empezar con Google" is the **white-fill** primary (currently `bg-white text-indigo-700`, migrated to `bg-white text-brand-dark`) and "Empezar con Microsoft" is the **translucent-dark** secondary (currently `bg-indigo-900/50 … border-indigo-400 text-white`, migrated to `bg-brand-dark/60 hover:bg-brand-dark/80 text-white border border-brand-cyan/40`). The existing 320 px single-line constraint and the `px-6 py-3 text-base` (below `sm`) / `px-8 py-4 text-lg` (`sm` and above) padding pattern from the prior `landing` spec requirements MUST be preserved verbatim.

#### Scenario: Hero keeps immersive dark treatment with new palette
- **WHEN** the home page is rendered
- **THEN** the hero `<section>` element resolves to a CSS `linear-gradient` whose stops include `brand.DEFAULT` (`#007BFF`), `brand.dark` (`#003D99`), and a `brand.cyan` (`#00E5FF`) stop at ≤ 40 % alpha
- **AND** the body text on the hero is white
- **AND** the headline uses the `text-display` font-size token (declared in `templates/base.html`) or its stepped fallback

#### Scenario: Hero subtitle uses brand.cloud, not brand.muted
- **WHEN** the home page is rendered
- **THEN** the subtitle paragraph beneath the hero headline uses `text-brand-cloud` (resolving to `#E6F2FF`)
- **AND** `text-brand-muted` does NOT appear on the subtitle element

#### Scenario: Hero CTAs preserve hierarchy and single-line behavior
- **WHEN** the home page is rendered at viewport 320 × 568
- **THEN** the "Empezar con Google" CTA has `bg-white` and `text-brand-dark` (replacing the prior `text-indigo-700`)
- **AND** the "Empezar con Microsoft" CTA has a translucent Cobalt fill (`bg-brand-dark/60`) and a `border-brand-cyan/40`
- **AND** both CTAs occupy a single line within their button at 320 px (preserving the prior `landing` requirement)
- **AND** the padding pattern `px-6 py-3 text-base` below `sm` / `px-8 py-4 text-lg` at `sm+` is preserved

### Requirement: Company-finder section adopts the new card chrome
The public company-finder section in `templates/home.html` SHALL be wrapped in a card surface using `bg-white border border-brand-muted rounded-2xl shadow-sm`, the live counter chip SHALL use `bg-brand-soft text-brand-dark font-semibold`, and the section's CTA "Ver paquetes y empezar" SHALL use the primary-fill button variant (`bg-brand hover:bg-brand-dark text-white`). All existing behavior requirements from the `landing` spec (allowed-options whitelist, no row-level data exposure, rate limit, target URL `/payments/paquetes/`, single-line-at-320 px) MUST continue to hold.

#### Scenario: Finder card uses new chrome without regressing behavior
- **GIVEN** an anonymous visitor on the home page
- **WHEN** the page is rendered
- **THEN** the finder section is wrapped in an element whose classes resolve to `bg-white`, `border-brand-muted`, `rounded-2xl`, and `shadow-sm`
- **AND** the live counter chip's classes resolve to `bg-brand-soft` background and `brand.dark` text
- **AND** the rendered HTML and any JSON fetched still contain only label strings and an integer count (no row-level data) — the prior `landing` privacy invariant is preserved

#### Scenario: "Cómo funciona" steps consume brand tokens consistently
- **WHEN** the home page is rendered
- **THEN** each of the four step-icon halos uses a `bg-brand-soft` or `bg-brand-muted` background and a `text-brand` glyph
- **AND** no `indigo-*` legacy class survives in this section

### Requirement: Filter option labels display in uppercase on Landing page
The company-finder filter widgets on the public landing page SHALL display all option labels —
both inside the dropdown list and inside the selected-value pills — in UPPERCASE. The underlying
option values sent to the API (for matching and counting) MUST remain unchanged (lowercase, as
stored in the database). The visual transformation MUST be achieved via CSS (`text-transform:
uppercase`) so that form submission values and whitelist validation are unaffected.

#### Scenario: Dropdown option labels appear in uppercase
- **GIVEN** the database contains areas `{"tecnología", "diseño"}`
- **WHEN** an anonymous visitor opens the Sector dropdown on the landing page
- **THEN** the dropdown list renders the labels as `TECNOLOGÍA` and `DISEÑO`
- **AND** the API count request still sends the lowercase values `tecnología` and `diseño`

#### Scenario: Selected pill labels appear in uppercase
- **GIVEN** the visitor has selected `"tecnología"` from the Sector dropdown
- **WHEN** the selection is confirmed
- **THEN** the pill inside the combobox input renders the text `TECNOLOGÍA`
- **AND** the hidden form input value for that selection remains `tecnología`

