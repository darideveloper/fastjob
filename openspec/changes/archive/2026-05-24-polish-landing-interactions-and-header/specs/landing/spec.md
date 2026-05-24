# landing delta — Polish landing interactions and filter UX

## ADDED Requirements

### Requirement: Filter widget placeholders signal type-to-search
The two filter combobox widgets in the public company-finder section of `templates/home.html` SHALL present placeholder text that explicitly tells the visitor the field is a hybrid search-and-pick control. The placeholder text MUST follow the pattern `Escribe o elige <noun> (ej. <example>)…`, where:

- the leading clause `Escribe o elige` signals that the visitor may type to filter, in addition to picking from the dropdown;
- the parenthetical example surfaces a real value from the existing whitelist, anchoring the visitor with a concrete cue.

The placeholders MUST be:

- Sector combobox: `Escribe o elige un sector (ej. Tecnología)…`
- Location combobox: `Escribe o elige una ubicación (ej. Madrid)…`

The placeholders MUST be supplied via the existing `data-placeholder` attribute on each combobox container in `templates/home.html` (read by `static/js/combobox.js` at initialization). The placeholders MUST remain in Spanish (matching the project's `LANGUAGE_CODE`). The example values (`Tecnología`, `Madrid`) MUST exist in the live whitelist returned by `GET /api/companies/filter-options/` so the cue is not misleading.

#### Scenario: Sector combobox shows the new placeholder
- **GIVEN** an anonymous visitor on the home page
- **WHEN** they focus the empty sector combobox (no selections yet)
- **THEN** the placeholder text reads exactly `Escribe o elige un sector (ej. Tecnología)…`
- **AND** the placeholder disappears when the visitor types or selects a pill (preserving the existing combobox behavior)

#### Scenario: Location combobox shows the new placeholder
- **GIVEN** an anonymous visitor on the home page
- **WHEN** they focus the empty location combobox (no selections yet)
- **THEN** the placeholder text reads exactly `Escribe o elige una ubicación (ej. Madrid)…`

#### Scenario: Placeholder example values are real whitelist members
- **WHEN** `GET /api/companies/filter-options/` is requested
- **THEN** the JSON response's `areas` list contains the string `Tecnología`
- **AND** the JSON response's `locations` list contains the string `Madrid`

### Requirement: Filter dropdowns show at least 8 selectable options without scrolling
Both filter combobox dropdowns (sector and location) in the public company-finder section SHALL display at least 8 **selectable** option rows simultaneously before requiring the visitor to scroll the list, **even when the dropdown also renders the "— Limpiar todos —" clear-all helper row at the top** (which occurs whenever the visitor has at least one pill selected). This MUST be achieved by raising the dropdown `<ul>` max-height in `static/js/combobox.js` from `max-h-48` (12 rem = 192 px, ≈ 5 visible rows at the current row height) to `max-h-96` (24 rem = 384 px, ≥ 9 visible rows at the current row height — guaranteeing 8 selectable options + 1 clear-all row when present). The existing `overflow-y-auto` MUST be preserved so the list continues to scroll when the whitelist exceeds the visible capacity.

The row styling (`px-3 py-2 text-sm`, ≈ 36 px per row) MUST be preserved. Increasing capacity MUST NOT change row density.

#### Scenario: Dropdown shows ≥ 8 selectable rows when the whitelist exceeds 8 values and no pill is selected
- **GIVEN** the `/api/companies/filter-options/` whitelist returns ≥ 10 sectors
- **AND** the visitor has not yet selected any sector pill (so the "— Limpiar todos —" row is NOT rendered)
- **WHEN** an anonymous visitor opens the sector dropdown on the home page
- **THEN** the dropdown `<ul>` exposes at least 8 selectable rows without requiring inner-list scrolling
- **AND** the 9th and 10th rows remain reachable via inner-list scroll

#### Scenario: Dropdown still shows ≥ 8 selectable rows when the "Limpiar todos" row is present
- **GIVEN** the whitelist returns ≥ 10 sectors
- **AND** the visitor has previously selected one sector pill (so the "— Limpiar todos —" helper row is rendered at the top of the dropdown)
- **WHEN** the visitor re-opens the sector dropdown
- **THEN** the dropdown exposes the "— Limpiar todos —" row plus at least 8 selectable rows without requiring inner-list scrolling
- **AND** the clear-all row is excluded from the "8 selectable" count

#### Scenario: Dropdown collapses naturally when the whitelist has fewer than 8 values
- **GIVEN** the whitelist returns only 3 locations
- **WHEN** the location dropdown opens
- **THEN** the dropdown renders only those 3 rows
- **AND** no empty padding is shown to "fill" the 384 px max-height

#### Scenario: Existing behavior preserved
- **WHEN** the visitor interacts with the dropdown (typing to filter, picking a value, removing a pill, "Limpiar todos")
- **THEN** every behavior defined under the "Public Company-Finder Section on Landing Page" requirement continues to hold
- **AND** the rendered HTML still exposes only label strings and the integer count (no row-level data)

### Requirement: Hero OAuth CTAs present distinct, brand-matched visual styles
The two hero OAuth CTAs in `templates/home.html` ("Empezar con Google" and "Empezar con Microsoft") SHALL present distinct brand-matched visual styles to ensure immediate differentiation at rest, while maintaining shared high-quality "lift" and "scale" interactions. Both CTAs MUST animate via a `transition` utility (≤ 200 ms).

Specifically:

- **"Empezar con Google"**: rendered as a clean white card at rest. On hover, it MUST gain `bg-brand-cloud` (`#E6F2FF`) and a brand-blue focus ring (`#4285F4` at 50% opacity via `hover:ring-4`). The contrast ratio (`#003D99` ink on `#E6F2FF` fill) MUST remain ≥ 4.5 : 1.
- **"Empezar con Microsoft"**: rendered as a bold dark card (`bg-gray-900`) with white text at rest. On hover, it MUST gain a brand-cyan focus ring (`#00A4EF` at 50% opacity via `hover:ring-4`).

Both CTAs MUST share the following interaction cues:
- On hover, they SHALL scale slightly (`hover:scale-[1.03]`) and lift vertically (`hover:-translate-y-1`).
- On hover, they SHALL deepen their elevation shadow to `shadow-2xl`.

Both CTAs MUST preserve every constraint already defined by the existing landing requirements: the 320 px single-line label, the `px-6 py-3 text-base` (below `sm`) / `px-8 py-4 text-lg` (`sm` and above) padding pattern, and the existing visual hierarchy relative to the surrounding gradient.

#### Scenario: Google CTA shows white-card style and brand-blue ring
- **GIVEN** the home page rendered
- **WHEN** the visitor views the "Empezar con Google" CTA at rest
- **THEN** it renders with a white background and `#003D99` (`brand.dark`) text
- **WHEN** the user hovers the CTA
- **THEN** it transitions to `#E6F2FF` (`brand.cloud`) background and applies a `ring-[#4285F4]/50` focus ring

#### Scenario: Microsoft CTA shows dark-card style and brand-cyan ring
- **GIVEN** the home page rendered
- **WHEN** the visitor views the "Empezar con Microsoft" CTA at rest
- **THEN** it renders with a `bg-gray-900` background and white text
- **WHEN** the user hovers the CTA
- **THEN** it applies a `ring-[#00A4EF]/50` focus ring

#### Scenario: Both CTAs exhibit high-quality hover transformations
- **WHEN** the user hovers either hero CTA
- **THEN** within ≤ 200 ms the button scales to `1.03x` its size
- **AND** it shifts exactly `1px` upward (`-translate-y-1`)
- **AND** its shadow elevation transitions to `shadow-2xl`

### Requirement: Company-finder CTA presents primary-fill hover treatment
The "Ver paquetes y empezar" CTA below the public company-finder section in `templates/home.html` SHALL present the primary-fill hover treatment defined by the ui-shell "Brand-matched hover affordance on every interactive control" requirement: on hover, the background transitions to `brand.dark` and a `shadow-md` (or stronger) elevation cue is applied, all via a `transition` of ≤ 200 ms.

The existing single-line-at-320-px constraint and the existing target URL (`/payments/paquetes/`) MUST be preserved unchanged.

#### Scenario: Company-finder CTA hover darkens and elevates
- **GIVEN** an anonymous visitor on the home page at viewport ≥ md
- **WHEN** the user hovers the "Ver paquetes y empezar" CTA
- **THEN** within ≤ 200 ms the background color transitions to `#003D99` (`brand.dark`)
- **AND** a `box-shadow` of at least `shadow-md` intensity is applied
- **AND** clicking the CTA still navigates to `/payments/paquetes/`

#### Scenario: Hover state respects single-line constraint at 320 px
- **GIVEN** an anonymous visitor at viewport 320 × 800 hovering the company-finder CTA
- **WHEN** the hover state is applied
- **THEN** the label "Ver paquetes y empezar" and its trailing arrow stay on the same single line (per the existing "Company-finder CTA fits on a single line at 320 px" requirement)
