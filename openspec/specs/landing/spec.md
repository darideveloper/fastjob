# landing Specification

## Purpose
TBD - created by archiving change add-company-filter-finder. Update Purpose after archive.
## Requirements
### Requirement: Public Company-Finder Section on Landing Page
The public landing page SHALL include a section, positioned **immediately below the hero section**, that lets anonymous visitors explore the company database by sector, sub-activity, and location. The section MUST consist of three searchable dropdown widgets (sector, sub-activity, and location) and a live counter showing the number of matching companies.

#### Scenario: Anonymous visitor sees the section with three dropdowns
- **WHEN** they load the landing page
- **THEN** the company-finder section contains three combobox widgets: Sector, Subactividad, and Ubicación.
- **AND** the widgets are populated with whitelist values from the database.

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
The company-finder filter widgets on the public landing page (Sector, Subactividad, and Ubicación) SHALL display all option labels — both inside the dropdown list and inside the selected-value pills — in UPPERCASE.

#### Scenario: Sub-area option labels appear in uppercase
- **GIVEN** the database contains sub-areas `{"productos de limpieza"}`
- **WHEN** an anonymous visitor opens the Subactividad dropdown on the landing page
- **THEN** the dropdown list renders the label as `PRODUCTOS DE LIMPIEZA`
- **AND** the "no filter" row renders as `— TODAS LAS SUBACTIVIDADES —`

### Requirement: Filter widget placeholders signal type-to-search
The three filter combobox widgets in the public company-finder section of `templates/home.html` SHALL present placeholder text that explicitly tells the visitor the field is a hybrid search-and-pick control. The placeholders MUST be:
- Sector combobox: `Escribe o elige un sector (ej. Tecnología)…`
- Location combobox: `Escribe o elige una ubicación (ej. Madrid)…`
- Sub-Area combobox: `Escribe o elige una subactividad (ej. Productos de limpieza)…`

#### Scenario: Sub-area combobox shows the new placeholder
- **WHEN** they focus the empty sub-area combobox
- **THEN** the placeholder text reads exactly `Escribe o elige una subactividad (ej. Productos de limpieza)…`

### Requirement: Filter dropdowns show at least 8 selectable options without scrolling
Both filter combobox dropdowns in the public company-finder section SHALL display at least 8 **selectable** option rows simultaneously before requiring the visitor to scroll the list.
Each combobox dropdown SHALL always render a **per-field "no filter" first option** as the first row in the dropdown, regardless of selection state. The label MUST be:
- Area combobox (`data-combobox="area"`): **"— TODOS LOS SECTORES —"**
- Location combobox (`data-combobox="location"`): **"— TODAS LAS UBICACIONES —"**
- Sub-Area combobox (`data-combobox="sub_area"`): **"— TODAS LAS SUBACTIVIDADES —"**

Clicking this row MUST clear all selected pills for that combobox (equivalent to removing the filter entirely) and update the company counter.

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
- Have a `min-height` equivalent to one line of text (`min-h-[1.25rem]` or equivalent `1.25rem`) so the layout never collapses even if content is briefly empty
- Pause (stop cycling) when any combobox input within the same `[data-filter-widget]` receives focus, and resume when all combobox inputs lose focus — **unless** the suggestion has already been permanently hidden due to user interaction

When a user first interacts with the filter widget (by focusing a combobox input or clicking the suggestion to pre-fill values), the suggestion SHALL fade out permanently with a `0.3s ease` opacity transition. Once hidden, the animation SHALL NOT restart or rebuild. This eliminates visual glitches from destroying and recreating the Typed.js instance on every filter change.

The suggestion SHALL NOT be rebuilt when cascading filter options change. The `rebuildSuggestions()` path triggered by `FastJobFilter.onOptionsChange` SHALL be removed entirely. Suggestions are decorative and generated from the full taxonomy at page-load time; they do not need to reflect the currently-narrowed filter state.

When `prefers-reduced-motion: reduce` is active, the element SHALL render a single static suggestion string (the first string from the shuffled list) with no animation, no cursor, and no Typed.js initialisation. This static string also hides on first user interaction.

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
- **AND** the suggestion element fades out permanently (opacity transitions to 0 over 0.3s)

#### Scenario: Animation pauses while a combobox is focused
- **GIVEN** the suggestion animation is actively cycling and has not been permanently hidden
- **WHEN** the visitor clicks into (or tabs into) either the area or location combobox input
- **THEN** the typing animation pauses (no further string transitions)

#### Scenario: Suggestion hides permanently on first filter interaction
- **GIVEN** the suggestion animation is actively cycling
- **WHEN** the visitor focuses either the area or location combobox input
- **THEN** the suggestion element fades out with a `0.3s ease` opacity transition
- **AND** the Typed.js instance is destroyed
- **AND** the suggestion element's innerHTML is cleared
- **AND** subsequent focus/blur cycles on the combobox inputs do NOT restart the animation

#### Scenario: No suggestion rebuild on filter change
- **GIVEN** the visitor has not yet interacted with the filter widget (suggestion is still visible)
- **WHEN** the available-filters API response updates the combobox option lists
- **THEN** the suggestion animation continues uninterrupted (no destroy+recreate cycle)
- **AND** there is no layout jump or vertical shift in the filter section

#### Scenario: Reduced-motion user sees a static suggestion
- **GIVEN** a visitor whose OS reports `prefers-reduced-motion: reduce`
- **WHEN** the landing page renders
- **THEN** the `<span data-search-suggestion>` displays a single static string (the first suggestion from the generated list)
- **AND** no typewriter animation or blinking cursor is visible
- **AND** Typed.js is NOT initialised (to avoid unnecessary JS overhead)
- **AND** the static suggestion also hides on first user interaction (focus or click)

#### Scenario: Fallback hint when too few filter options exist
- **GIVEN** the `/api/companies/filter-options/` response returns fewer than 2 areas or fewer than 2 locations
- **WHEN** the suggestion module initialises
- **THEN** the `<span data-search-suggestion>` displays the static text `"Busca por sector y ubicación"`
- **AND** the element is not interactive (no click handler, no combobox fill)
- **AND** the element has `min-height: 1.25rem` so the layout does not collapse

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

### Requirement: Combobox input loses focus after selecting a filter option on the landing page

When the visitor selects an option from either the area or location combobox dropdown on the landing page (including the "— TODOS LOS SECTORES —" / "— TODAS LAS UBICACIONES —" clear row), the combobox text input MUST lose focus (blur). This ensures:

- The blinking cursor disappears (no ambiguous "cursor with no dropdown" state)
- The dropdown stays closed until the visitor explicitly interacts with the control again
- When the visitor clicks the control wrapper or the input, the existing `focus` event handler re-opens the dropdown with fully refreshed options (excluding already-selected values)

The blur MUST be triggered imperatively via `textInput.blur()` inside the `mousedown` event handler, after the selection has been processed and the dropdown has been hidden. The existing `e.preventDefault()` call in the `mousedown` handler MUST be preserved so the input does not lose focus to the browser's default mousedown behavior before the imperative blur takes effect.

Keyboard selection (Enter key on a highlighted item) MUST produce the same result: after the synthetic `mousedown` event is dispatched and handled, the input MUST lose focus.

#### Scenario: Selecting a filter option removes cursor and closes dropdown

- **GIVEN** an anonymous visitor on the landing page
- **WHEN** they open the area combobox dropdown and click `TECNOLOGÍA`
- **THEN** the `TECNOLOGÍA` pill is added to the combobox
- **AND** the dropdown closes
- **AND** the text input loses focus (no blinking cursor)
- **AND** `document.activeElement` is NOT the combobox text input

#### Scenario: Clicking "clear all" removes cursor and closes dropdown

- **GIVEN** an anonymous visitor on the landing page with `TECNOLOGÍA` selected
- **WHEN** they open the area combobox dropdown and click `— TODOS LOS SECTORES —`
- **THEN** the `TECNOLOGÍA` pill is removed
- **AND** the dropdown closes
- **AND** the text input loses focus

#### Scenario: Clicking the control after selection re-opens the dropdown

- **GIVEN** an anonymous visitor who just selected `TECNOLOGÍA` from the area combobox
- **WHEN** they click the combobox control wrapper (or the text input)
- **THEN** the dropdown re-opens showing all area options except `TECNOLOGÍA` (already selected)
- **AND** the cursor reappears in the text input

#### Scenario: Keyboard Enter selection also blurs the input

- **GIVEN** an anonymous visitor on the landing page with keyboard focus on the area combobox
- **WHEN** they press ArrowDown to highlight the first option and press Enter
- **THEN** the option is selected and the text input loses focus (same behavior as mouse click)

### Requirement: Landing page renders a FAQs section at the bottom

The public landing page (`templates/home.html`) SHALL render a Frequently Asked Questions (FAQs) section as its **final** in-content section, positioned immediately after the pricing teaser section (`#paquetes`) and before the page footer.

The section MUST include:
- A clear heading (e.g., "Preguntas frecuentes").
- A brief descriptive subtitle.
- A list of collapsible FAQ cards containing static questions and answers about the product.

The FAQ cards MUST be implemented using semantic HTML `<details>` and `<summary>` elements to ensure native accessibility, keyboard navigation, and zero-JavaScript operation. The cards MUST be styled using the project's Tailwind CSS utilities to match the brand identity (e.g., `bg-white`, `rounded-2xl`, `border-brand-muted`). The `<summary>` element MUST display an indicator (like a chevron or plus/minus icon) that visually reflects the expanded/collapsed state using CSS (e.g., via `group-open` modifier in Tailwind).

**New Specifications:**
- Each FAQ item MUST have a unique `id` attribute (e.g., `id="faq-segmento"`) to support deep-linking.
- The section container MUST have `scroll-margin-top` (e.g., `scroll-mt-20`) to ensure anchor navigation does not hide the section behind fixed headers.
- The disclosure indicator MUST be hidden from assistive technologies using `aria-hidden="true"`.
- Typography MUST use balanced wrapping (`text-wrap: balance` or `text-pretty`) on headings and proper curly quotes (`“ ”`) for text.
- Animations MUST respect the `prefers-reduced-motion` media query.

#### Scenario: FAQs section appears after the pricing teaser
- **WHEN** an anonymous or authenticated visitor loads `/`
- **THEN** the rendered HTML contains a `<section>` with `id="faqs"` and `scroll-mt-20`
- **AND** the section is placed after the `#paquetes` section and before the end of the `content` block

#### Scenario: FAQs are natively collapsible and accessible
- **WHEN** the visitor scrolls to the FAQs section
- **THEN** the FAQ items are rendered as `<details>` elements with unique IDs
- **AND** the question text is wrapped in a `<summary>` element with visible focus states
- **AND** clicking the `<summary>` expands the card to reveal the answer text
- **AND** the component operates fully without any custom JavaScript

#### Scenario: FAQ cards align with the brand style
- **WHEN** the FAQs section is rendered
- **THEN** the individual FAQ cards have a border (`border-brand-muted`) and rounded corners (`rounded-2xl` or similar)
- **AND** an icon or chevron indicates whether the card is open or closed and is hidden from ARIA

