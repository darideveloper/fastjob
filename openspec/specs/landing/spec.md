# landing Specification

## Purpose
TBD - created by archiving change add-company-filter-finder. Update Purpose after archive.
## Requirements
### Requirement: Public Company-Finder Section on Landing Page

The public landing page SHALL include a section, positioned **immediately below the hero section**, that lets anonymous visitors explore the company database by sector and location. The section MUST be 100% functional without authentication. It MUST consist of two searchable dropdown widgets (sector and location) and a live counter showing the number of matching companies. The widgets' option lists MUST be sourced from the same allowed-options whitelist as the dashboard. The counter MUST display only an integer and MUST NOT expose any company name, email, primary key, or other row-level data anywhere in the rendered HTML or JavaScript.

When the section's backing API requests fail (rate limit `429`, server error, or network failure), the section MUST degrade gracefully and visibly: it MUST NOT silently render empty, non-functional dropdowns. The visitor MUST be shown a recoverable error state with a retry affordance.

#### Scenario: Anonymous visitor sees the section without logging in

- **GIVEN** a visitor with no authenticated session
- **WHEN** they load the landing page
- **THEN** the company-finder section is rendered immediately below the hero section, with both dropdowns populated and a placeholder counter

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
taglines, button labels, and the "How it works" step list). The landing
page SHALL also avoid the strings `enlace de descarga` / `enlaces de
descarga` (see also the new `Landing page reflects the CV-attachment
delivery model` requirement above): the product now ships the CV as a
PDF attachment, so any link-based phrasing is factually wrong. When a
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

The "no filter" first row ("— TODOS LOS SECTORES —" / "— TODAS LAS UBICACIONES —") MUST also appear in uppercase and MUST be subject to the same CSS `text-transform: uppercase` rule as other dropdown items.

#### Scenario: Dropdown option labels appear in uppercase
- **GIVEN** the database contains areas `{"tecnología", "diseño"}`
- **WHEN** an anonymous visitor opens the Sector dropdown on the landing page
- **THEN** the dropdown list renders the labels as `TECNOLOGÍA` and `DISEÑO`
- **AND** the "no filter" row renders as `— TODOS LOS SECTORES —`
- **AND** the API count request still sends the lowercase values `tecnología` and `diseño`

#### Scenario: Selected pill labels appear in uppercase
- **GIVEN** the visitor has selected `"tecnología"` from the Sector dropdown
- **WHEN** the selection is confirmed
- **THEN** the pill inside the combobox input renders the text `TECNOLOGÍA`
- **AND** the hidden form input value for that selection remains `tecnología`

#### Scenario: Backend validation is unaffected by uppercase display
- **GIVEN** the current allowed-options list for `area` contains `"tecnología"` (lowercase)
- **WHEN** the user submits the filter form after selecting the option displayed as `TECNOLOGÍA`
- **THEN** the server accepts the submission (hidden input value is `tecnología`, which matches
  the whitelist)
- **AND** the user's `area_filters` is updated to `["tecnología"]`

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
Both filter combobox dropdowns (sector and location) in the public company-finder section SHALL display at least 8 **selectable** option rows simultaneously before requiring the visitor to scroll the list, **even when the dropdown also renders the per-field "no filter" first option at the top**. This MUST be achieved by setting the dropdown `<ul>` max-height in `static/js/combobox.js` to `max-h-[480px]` (480 px, ≥ 13 visible rows at the current row height — guaranteeing 8 selectable options + 1 "no filter" row when present, with room for additional rows). The existing `overflow-y-auto` MUST be preserved so the list continues to scroll when the whitelist exceeds the visible capacity.

Each combobox dropdown SHALL always render a **per-field "no filter" first option** as the first row in the dropdown, regardless of selection state. The label MUST be:
- Area combobox (`data-combobox="area"`): **"— TODOS LOS SECTORES —"**
- Location combobox (`data-combobox="location"`): **"— TODAS LAS UBICACIONES —"**

Clicking this row MUST clear all selected pills for that combobox (equivalent to removing the filter entirely) and update the company counter. The row MUST be excluded from keyboard navigation (ArrowUp/ArrowDown/Enter) by applying the `italic` class so the existing `li:not(.italic)` selector skips it. The row MUST be styled distinctly from regular selectable options (e.g. `text-brand-dark font-semibold border-b border-gray-100`) and MUST be displayed in uppercase via the existing CSS `text-transform: uppercase` rule.

The previous conditional "— Limpiar todos —" row (shown only when `selected.length > 0`) and the "Todos seleccionados" fallback message MUST be removed, as the "no filter" option subsumes their functionality.

#### Scenario: "No filter" option is always visible in the area dropdown
- **GIVEN** the `/api/companies/filter-options/` whitelist returns at least 1 sector
- **WHEN** an anonymous visitor opens the sector dropdown on the landing page
- **THEN** the first row in the dropdown displays "— TODOS LOS SECTORES —"
- **AND** this row is visible regardless of whether any pills are selected

#### Scenario: "No filter" option is always visible in the location dropdown
- **GIVEN** the `/api/companies/filter-options/` whitelist returns at least 1 location
- **WHEN** an anonymous visitor opens the location dropdown on the landing page
- **THEN** the first row in the dropdown displays "— TODAS LAS UBICACIONES —"
- **AND** this row is visible regardless of whether any pills are selected

#### Scenario: Clicking "no filter" clears all pills and updates the counter
- **GIVEN** the visitor has selected "Tecnología" and "Diseño" in the sector dropdown
- **WHEN** the visitor clicks the "— TODOS LOS SECTORES —" row
- **THEN** both pills are removed from the sector combobox
- **AND** the company counter updates to reflect the count without any area filter
- **AND** no hidden inputs for `area_filter` are submitted in a form POST

#### Scenario: Clicking "no filter" when no pills are selected is a no-op
- **GIVEN** the visitor has not selected any sector pills
- **WHEN** the visitor clicks the "— TODOS LOS SECTORES —" row
- **THEN** the dropdown closes and no change occurs (already in the "no filter" state)

#### Scenario: Clicking "no filter" clears the search text
- **GIVEN** the visitor has typed "tecn" into the sector combobox input and the dropdown is showing filtered results
- **WHEN** the visitor clicks the "— TODOS LOS SECTORES —" row
- **THEN** the search input is cleared (`textInput.value` becomes `""`)
- **AND** all pills are removed (if any were selected)
- **AND** the dropdown closes
- **AND** the next focus/reopen of the dropdown shows all options, not the filtered subset

#### Scenario: "No filter" row is visible during search/typing
- **GIVEN** the visitor has typed "mad" into the location combobox
- **WHEN** the dropdown renders the filtered list of locations matching "mad"
- **THEN** the "— TODAS LAS UBICACIONES —" row still appears as the first row in the dropdown (above the filtered results)

#### Scenario: Dropdown shows ≥ 8 selectable rows when the whitelist exceeds 8 values
- **GIVEN** the `/api/companies/filter-options/` whitelist returns ≥ 10 sectors
- **WHEN** an anonymous visitor opens the sector dropdown on the home page
- **THEN** the dropdown `<ul>` exposes the "— TODOS LOS SECTORES —" row plus at least 8 selectable sector rows without requiring inner-list scrolling
- **AND** the 9th and 10th rows remain reachable via inner-list scroll

#### Scenario: Dropdown collapses naturally when the whitelist has fewer than 8 values
- **GIVEN** the whitelist returns only 3 locations
- **WHEN** the location dropdown opens
- **THEN** the dropdown renders the "— TODAS LAS UBICACIONES —" row plus those 3 rows
- **AND** no empty padding is shown to "fill" the max-height

#### Scenario: Keyboard navigation skips the "no filter" row
- **GIVEN** the sector dropdown is open showing the "— TODOS LOS SECTORES —" row followed by sector options
- **WHEN** the user presses ArrowDown from the text input
- **THEN** focus highlights the first **selectable** sector option (the second `<li>`), not the "no filter" row
- **AND** pressing ArrowUp from the first selectable option returns focus to the text input, not the "no filter" row
- **AND** pressing Enter while no selectable option is highlighted does not activate the "no filter" row

#### Scenario: "No filter" row labels are displayed in uppercase
- **GIVEN** the combobox dropdown is rendered in either the landing page or the dashboard
- **WHEN** the "no filter" row is visible
- **THEN** the text "— TODOS LOS SECTORES —" or "— TODAS LAS UBICACIONES —" appears in uppercase
- **AND** the underlying label text in `combobox.js` uses the uppercaseSpanish form directly (not relying solely on CSS transform, though CSS `text-transform: uppercase` may also apply)

#### Scenario: Existing behavior preserved
- **WHEN** the visitor interacts with the dropdown (typing to filter, picking a value, removing a pill)
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

### Requirement: Landing page reflects the CV-attachment delivery model
The public landing page (`templates/home.html`) SHALL describe the product as sending the CV **as a PDF attachment**, not as a download link. The strings `enlace de descarga`, `enlaces de descarga`, and `Sin adjuntos` MUST NOT appear in the rendered HTML of `/` after this change. The replacement copy MUST stay accurate to the delivery flow established by `apps/mailing/migrations/0008_auto_20260514_0522.py` (the CV ships as a PDF attached to the outbound email).

#### Scenario: Hero subtitle describes attachment delivery, not link delivery
- **GIVEN** an anonymous visitor at any viewport
- **WHEN** they request `GET /` and the response body is rendered
- **THEN** the hero subtitle paragraph contains the substring `PDF adjunto` (or `en adjunto`)
- **AND** a case-insensitive regex search of the rendered HTML for `enlaces? de descarga` returns zero matches

#### Scenario: Trust-signal card no longer claims "Sin adjuntos"
- **WHEN** the landing page renders the deliverability trust-signal grid
- **THEN** no card on that grid contains the heading `Sin adjuntos`
- **AND** the card that previously carried that heading now describes the PDF-attachment behavior in a positive frame (e.g. `CV en PDF adjunto`)

### Requirement: Landing page renders a pricing-teaser section at the bottom

The public landing page SHALL render a "Paquetes" section as its **final** in-content section, positioned above the page footer. The section MUST iterate the same active `CreditPackage` rows surfaced by `apps/payments/views.py:packages()`, ordered by `price_eur`, and MUST use card chrome visually identical to `templates/payments/packages.html` so a visitor scrolling the landing sees the same pricing surface they would see on `/payments/paquetes/`.

Card markup is extracted into a shared partial `templates/payments/_package_card.html` used by both the landing page and the canonical pricing page. The landing CTAs use the **same auth-gated behavior** as `/payments/paquetes/`: anonymous users see a login-redirect link (`/accounts/login/?next=/payments/paquetes/`), authenticated users POST to Stripe checkout (`{% url 'create_checkout' package.pk %}`). The landing and pricing pages now render identical card chrome and behavior via a single shared partial.

#### Scenario: Pricing teaser appears as the last in-content section

- **GIVEN** at least one active `CreditPackage` row in the database
- **WHEN** an anonymous or authenticated visitor loads `/`
- **THEN** the rendered HTML contains a `<section>` with `id="paquetes"` placed after the trust-signals section and before the page footer
- **AND** that section renders one card per active package, ordered by `price_eur` ascending

#### Scenario: Cards reuse the canonical pricing chrome

- **WHEN** the landing pricing teaser renders
- **THEN** each card's classes resolve to `bg-white`, `rounded-2xl`, `border-brand-muted`, and `p-6` (matching `templates/payments/packages.html`)
- **AND** the recommended card (currently the second card) carries `shadow-lg` and `ring-2 ring-brand-dark` plus a ribbon with the label `Más popular`

#### Scenario: Landing CTAs use the same auth-gated behavior as /payments/paquetes/

- **GIVEN** an **authenticated** user with `is_authenticated = True`
- **WHEN** they load `/`
- **THEN** every CTA inside the pricing teaser is a `<form method="post" action="/payments/create-checkout/...">` (same as the canonical pricing page)
- **GIVEN** an **anonymous** visitor
- **WHEN** they load `/`
- **THEN** every CTA inside the pricing teaser is an `<a>` whose `href` starts with `/accounts/login/?next=/payments/paquetes/` (matching `/payments/paquetes/` anonymous behavior)

#### Scenario: Teaser hides cleanly when no packages exist

- **GIVEN** zero active `CreditPackage` rows
- **WHEN** the landing page renders
- **THEN** the `#paquetes` section is either omitted entirely or shows a neutral "Próximamente disponibles" placeholder — it MUST NOT show an empty 3-column grid skeleton

### Requirement: Landing-page error pages and cv-link templates use neutral copy
Templates rendered by the legacy `cv_download` view (`templates/mailing/cv_not_found.html`, `templates/mailing/cv_revoked.html`) SHALL use copy that does NOT reference "enlace de descarga" or "descarga revocada". The view itself remains operational so historical email links keep resolving; only the rendered strings change.

#### Scenario: cv_not_found page uses neutral phrasing
- **WHEN** a client requests `GET /cv/<unknown-token>/` and the `cv_not_found.html` template renders
- **THEN** the rendered HTML does NOT contain the substring `enlace de descarga`
- **AND** the subtitle paragraph reads `Este enlace ya no está disponible o ha expirado.`

#### Scenario: cv_revoked page uses neutral phrasing
- **WHEN** a client follows a link whose `MailingLog` has been revoked and `cv_revoked.html` renders
- **THEN** the `<title>` reads `Enlace revocado — FastJob` (not `Descarga revocada — FastJob`)
- **AND** the subtitle paragraph reads `Este enlace ya no está disponible porque el destinatario ha cancelado la suscripción.`
- **AND** neither the heading nor the body contains the substring `La descarga ya no está disponible`

### Requirement: Search-suggestion animation in the company-finder section
The public landing page company-finder section (`templates/home.html`) SHALL render a typewriter-animated suggestion element (`<span data-search-suggestion>`) immediately below the section subtitle (`<p>`) and above the filter card. The element SHALL display cycling strings in the format `"{Area} en {Location}..."` — for example, `"Abogados en Madrid..."` — where `{Area}` and `{Location}` are real values drawn from the `/api/companies/filter-options/` response. The animation SHALL be powered by the vendored Typed.js library (`static/js/vendor/typed.min.js`), initialised by `static/js/search-suggestion.js`.

The suggestion element SHALL:
- Use `text-brand` colour with `hover:text-brand-dark transition` to signal clickability (the element has `cursor-pointer`)
- Carry `aria-hidden="true"` so screen readers skip the transient animation
- Pause (stop cycling) when any combobox input within the same `[data-filter-widget]` receives focus, and resume when all combobox inputs lose focus

When `prefers-reduced-motion: reduce` is active, the element SHALL render a single static suggestion string (the first string from the shuffled list) with no animation, no cursor, and no Typed.js initialisation.

The suggestion strings SHALL be generated from 8-12 random combinations of areas and locations from the filter-options response. If the response contains fewer than 2 areas or fewer than 2 locations, the element SHALL fall back to a static hint: `"Busca por sector y ubicación"`.

#### Scenario: Animated suggestion renders under the section heading
- **GIVEN** an anonymous visitor on the home page at viewport 1280 × 800
- **WHEN** the company-finder section renders
- **THEN** a `<span data-search-suggestion>` element appears immediately below the section subtitle `<p>` and above the filter card
- **AND** the element displays a typewriter-animated string in the format `"{Area} en {Location}..."` (e.g. `"Abogados en Madrid..."`)
- **AND** the element's text colour resolves to `brand.DEFAULT` (`#007BFF`)

#### Scenario: Clicking the suggestion pre-fills the comboboxes and updates the count
- **GIVEN** the animated suggestion currently displays `"Abogados en Madrid..."`
- **AND** `"Abogados"` is a valid area in the whitelist
- **AND** `"Madrid"` is a valid location in the whitelist
- **WHEN** the visitor clicks the suggestion element
- **THEN** the area combobox gains the value `"abogados"` (matching the whitelist)
- **AND** the location combobox gains the value `"Madrid"` (matching the whitelist)
- **AND** the company counter updates to reflect the combined filter (triggered by the combobox's existing `onChange` callback)
- **AND** the page does NOT navigate away (the user remains on the landing page)

#### Scenario: Animation pauses while a combobox is focused
- **GIVEN** the suggestion animation is actively cycling
- **WHEN** the visitor clicks into (or tabs into) either the area or location combobox input
- **THEN** the typing animation pauses (no further string transitions)
- **WHEN** the visitor unfocuses (blurs) the combobox input
- **THEN** the animation resumes from where it paused

#### Scenario: Reduced-motion user sees a static suggestion
- **GIVEN** a visitor whose OS reports `prefers-reduced-motion: reduce`
- **WHEN** the landing page renders
- **THEN** the `<span data-search-suggestion>` displays a single static string (the first suggestion from the generated list)
- **AND** no typewriter animation or blinking cursor is visible
- **AND** Typed.js is NOT initialised (to avoid unnecessary JS overhead)

#### Scenario: Fallback hint when too few filter options exist
- **GIVEN** the `/api/companies/filter-options/` response returns fewer than 2 areas or fewer than 2 locations
- **WHEN** the suggestion module initialises
- **THEN** the `<span data-search-suggestion>` displays the static text `"Busca por sector y ubicación"`
- **AND** the element is not interactive (no click handler, no combobox fill)

#### Scenario: Suggestion element is hidden from screen readers
- **GIVEN** a screen-reader user navigating the landing page
- **WHEN** the company-finder section is encountered
- **THEN** the `<span data-search-suggestion>` element has `aria-hidden="true"`
- **AND** the screen reader announces the section heading and the combobox placeholders (which already contain type-to-search hints) but skips the animated suggestion

### Requirement: Features section uses a distinct background after company-finder reorder
The "¿Cómo funciona?" features section in `templates/home.html` SHALL use `bg-gray-50` as its background class to maintain visual separation from the company-finder section immediately above it. Since the company-finder section sits directly above the features section (after the reorder), both would otherwise share a white/default background with no visual break between them.

#### Scenario: Features section renders with a light-gray background
- **GIVEN** an anonymous visitor on the home page
- **WHEN** they scroll past the company-finder section to the features section
- **THEN** the features `<section>` element has the `bg-gray-50` class
- **AND** there is a visible contrast between the white company-finder background and the light-gray features background

