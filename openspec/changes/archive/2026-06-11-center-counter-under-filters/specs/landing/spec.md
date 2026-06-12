## MODIFIED Requirements

### Requirement: Company-finder section adopts the new card chrome
The public company-finder section in `templates/home.html` SHALL be wrapped in a card surface using `bg-white border border-brand-muted rounded-2xl shadow-sm`. The three filter widgets (Ubicación, Sector / Área, and Subactividad) MUST be organized in a horizontal grid/row layout on desktop (`md` and above) and stack vertically on mobile. The company counter box MUST be positioned directly above the filters, centered horizontally, and styled with `bg-brand-soft text-brand-dark font-semibold`. All existing behavior requirements from the `landing` spec (allowed-options whitelist, no row-level data exposure, rate limit, target URL `/payments/paquetes/`, single-line-at-320 px) MUST continue to hold.

#### Scenario: Finder card uses new chrome without regressing behavior
- **GIVEN** an anonymous visitor on the home page
- **WHEN** the page is rendered
- **THEN** the finder section is wrapped in an element whose classes resolve to `bg-white`, `border-brand-muted`, `rounded-2xl`, and `shadow-sm`
- **AND** the three combobox filters occupy the bottom row in a 3-column layout on desktop (ordered: Ubicación, Sector / Área, Subactividad)
- **AND** the company counter is centered directly above the combobox filters
- **AND** the live counter chip's classes resolve to `bg-brand-soft` background and `brand.dark` text
- **AND** the rendered HTML and any JSON fetched still contain only label strings and an integer count (no row-level data) — the prior `landing` privacy invariant is preserved

#### Scenario: "Cómo funciona" steps consume brand tokens consistently
- **WHEN** the home page is rendered
- **THEN** each of the four step-icon halos uses a `bg-brand-soft` or `bg-brand-muted` background and a `text-brand` glyph
- **AND** no `indigo-*` legacy class survives in this section
