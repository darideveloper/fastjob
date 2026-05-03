# dashboard Specification

## Purpose
TBD - created by archiving change add-company-filter-finder. Update Purpose after archive.
## Requirements
### Requirement: Search Filters Use DB-Backed Dropdowns
The dashboard "Sector / Área" and "Ubicación" inputs SHALL be searchable dropdowns whose option lists are sourced exclusively from the distinct values of `Company.area` and `Company.location` in the database. Users MUST NOT be able to persist a filter value that is not currently present in the allowed-options whitelist. An empty selection MUST mean "no filter on that field".

#### Scenario: Dropdown options reflect the current database state
- **GIVEN** the `Company` table contains exactly three distinct non-empty `area` values: `"Tecnología"`, `"Diseño"`, `"Marketing"`
- **WHEN** a logged-in user opens the dashboard
- **THEN** the "Sector / Área" dropdown lists exactly those three values (in alphabetical order)

#### Scenario: User cannot persist a free-text value
- **GIVEN** the current allowed-options list for `area` does NOT contain the value `"Pesca"`
- **WHEN** the user submits the filter form with `area_filter=Pesca` (e.g. via a hand-crafted POST)
- **THEN** the server rejects the submission with an error message
- **AND** the user's stored `area_filter` remains unchanged

#### Scenario: Empty selection clears the filter
- **WHEN** the user submits the filter form with `area_filter=` (empty string)
- **THEN** the user's stored `area_filter` is set to the empty string
- **AND** the mailing engine treats the user as having no `area` filter

### Requirement: Live Company-Match Counter on Dashboard
The dashboard SHALL display a live counter, immediately below the filter form, showing the number of companies that match the currently-selected filter values. The counter MUST update whenever either dropdown value changes, MUST display only an integer (no company names, emails, or row data), and MUST source its number from the public count endpoint (so engine and counter cannot drift).

#### Scenario: Counter updates when filters change
- **GIVEN** the dashboard counter currently reads `42` for `area=""` and `location=""`
- **WHEN** the user selects `area="Tecnología"` from the dropdown
- **THEN** the counter re-fetches and displays the new count for `area="Tecnología"` within roughly one debounce window (~250 ms after selection)

#### Scenario: Counter shows an integer only
- **WHEN** the counter renders for any filter combination
- **THEN** the rendered text contains only a non-negative integer
- **AND** no part of the response body or DOM exposes a company name, email, or primary key

#### Scenario: Counter agrees with the mailing engine
- **GIVEN** a user has set `area_filter="Tecnología"` and `location_filter="Madrid"`
- **AND** the dashboard counter reads `0`
- **WHEN** the slow-drip task runs for that user
- **THEN** the engine sends nothing for that user (because the eligible-company queryset is empty by the same matching rules)

### Requirement: Activity table is horizontally scrollable on small viewports
The recent-activity table in `templates/dashboard/index.html` SHALL render at a fixed minimum width such that the existing `overflow-x-auto` wrapper engages on viewports below 640 px. Cell content (company email, template name, date, status badge) MUST NOT wrap mid-word, and status badges (`Enviado`, `Fallido`) MUST NOT clip to truncated forms (e.g. `Enviad…`, `Fallid…`).

#### Scenario: Activity table horizontal-scrolls at 320 px with seeded data
- **GIVEN** a logged-in user with at least three `MailingLog` rows (one each for sent and failed statuses) at viewport 320 × 800
- **WHEN** the dashboard page is rendered
- **THEN** the `<table>` element's `scrollWidth` is at least 640 px
- **AND** the wrapping `<div class="overflow-x-auto">` exposes a horizontal scrollbar (or scroll affordance)
- **AND** every status badge renders its full label (`Enviado` or `Fallido`) without text clipping

#### Scenario: Activity table at 768 px renders without horizontal scroll
- **GIVEN** the same seeded data at viewport 768 × 1024
- **WHEN** the dashboard page is rendered
- **THEN** the activity table fits without horizontal overflow inside its column
- **AND** no cell wraps to multiple lines

### Requirement: CV-list rows stack vertically on small viewports
Each item in the "Tus CVs" list (`<li>` rows containing the CV title, date, and per-row actions "Activo" / "Usar" / "Eliminar") SHALL stack the actions below the title on viewports below 640 px (`sm`), and SHALL render them side-by-side at `sm` and above. Long CV names MUST NOT push the actions off-screen at 320 px.

#### Scenario: Long CV name on a 320 px viewport stacks the actions below
- **GIVEN** a logged-in user with a CV named "Mi CV Senior Backend Developer Full Stack" at viewport 320 × 800
- **WHEN** the dashboard page is rendered
- **THEN** the title `<p>` and the actions `<div>` render on separate lines
- **AND** every action button is fully visible within the viewport (no element has `getBoundingClientRect().right > 320`)

#### Scenario: Same row at 768 px renders side-by-side
- **GIVEN** the same CV at viewport 768 × 1024
- **WHEN** the dashboard page is rendered
- **THEN** the title and the actions `<div>` are on the same line
- **AND** the visual layout is byte-equivalent to today's

### Requirement: Credit-card stat link row wraps gracefully
The link row inside the "Envíos disponibles" stat card (containing the "Comprar más →" link and the "Facturación" billing-portal form) SHALL use `flex-wrap`, so its contents wrap onto a second line rather than overflowing the card on cramped widths or with longer translations.

#### Scenario: Link row wraps to two lines when the card is narrowed
- **GIVEN** the dashboard rendered with the credit-card stat card constrained to 240 px width
- **WHEN** the row is laid out
- **THEN** the "Comprar más →" link and the "Facturación" button render on two lines
- **AND** neither element extends past the card's right padding

### Requirement: File-input control is replaced by a styled label
The "Subir CV" form's `<input type="file">` SHALL be hidden visually (`class="sr-only"` while remaining keyboard-accessible) and presented through a styled `<label>` that visually matches the rest of the design system (brand button styling). The currently selected filename MUST be shown in Spanish (`Sin archivo seleccionado` when empty, otherwise the selected filename) in a sibling `<span>` updated by an inline `change` listener. The native browser-rendered `Choose File / No file chosen` text MUST NOT appear anywhere on the page.

#### Scenario: Initial state shows the Spanish placeholder
- **GIVEN** a logged-in user opens the dashboard
- **WHEN** the page first renders
- **THEN** the file-input control's visible label is the styled brand label
- **AND** the sibling filename span reads exactly `Sin archivo seleccionado`
- **AND** the rendered HTML contains no occurrence of the strings `Choose File` or `No file chosen` (verified via locale-independent test)

#### Scenario: After selecting a file, the filename appears
- **GIVEN** the dashboard is rendered and the user clicks the styled label
- **WHEN** the user picks `mi-cv.pdf` in the OS file picker
- **THEN** the filename span updates to `mi-cv.pdf`
- **AND** the underlying `<input type="file">` retains the selected file (so form submission proceeds normally)

### Requirement: Delete-account form stacks the destructive action below the back link on small viewports
On `templates/dashboard/delete_account.html`, the button row currently rendering "← Volver" on the left and the red "Eliminar permanentemente" button on the right SHALL stack the destructive button below the back link on viewports below 640 px (`flex-col-reverse sm:flex-row`). This both fixes the 2-line wrap of the destructive button at 320 px and reduces the chance of accidental destructive taps on mobile.

#### Scenario: Buttons stack with the destructive action below at 320 px
- **GIVEN** a logged-in user at viewport 320 × 800
- **WHEN** they navigate to `/dashboard/eliminar-cuenta/`
- **THEN** the "← Volver" link renders above the "Eliminar permanentemente" button
- **AND** both render on a single line each (no internal wrap)

#### Scenario: Buttons render side-by-side at 640 px
- **GIVEN** viewport 640 × 800
- **WHEN** the delete-account page is rendered
- **THEN** "← Volver" is on the left and "Eliminar permanentemente" is on the right
- **AND** the layout is byte-equivalent to today's

### Requirement: Dashboard surfaces use "envíos" terminology
The authenticated dashboard surface SHALL use the noun `envío` / `envíos`
(singular / plural) in every user-visible string — including the global
navbar chip in `templates/base.html`, the stat-card heading in
`templates/dashboard/index.html`, and any flash message emitted by
`apps/dashboard/views.py` — and MUST NOT render the literal substring
`crédito` / `créditos` (any case, with or without the acute accent) in
the dashboard's HTML or in queued messages-framework text. The numeric
value displayed next to the noun MUST continue to be sourced from
`User.credits_remaining`; the underlying field is intentionally NOT
renamed, only the noun rendered next to its value changes.

#### Scenario: Authenticated navbar chip shows "envíos"
- **GIVEN** an authenticated user with `credits_remaining = 7`
- **WHEN** any page extending `base.html` is rendered for that user
- **THEN** the navbar chip renders the text `7 envíos`
- **AND** the chip does NOT contain the substring `créditos`

#### Scenario: Dashboard stat card heading is "Envíos disponibles"
- **GIVEN** an authenticated user opens `GET /dashboard/`
- **WHEN** the stat-card row at the top of the dashboard is rendered
- **THEN** the card label above the integer reads `Envíos disponibles`
- **AND** the rendered HTML contains no occurrence of the regex
  `[Cc]r[ée]dito`

#### Scenario: "No credits" flash message uses "envíos"
- **GIVEN** an authenticated user with `credits_remaining = 0`, a
  linked OAuth provider, and an active CV
- **WHEN** the user submits `POST /dashboard/toggle-campaign/` with
  `action=start`
- **THEN** a Django messages-framework `error` is queued whose body is
  `"No tienes envíos disponibles. Compra un paquete para continuar."`
- **AND** no other queued message text references the word "crédito"

#### Scenario: Internal field name is intentionally preserved
- **GIVEN** the model field `User.credits_remaining` (defined at
  `apps/accounts/models.py:11`)
- **WHEN** any dashboard template renders the user's balance
- **THEN** the template still reads the value via
  `{{ user.credits_remaining }}`
- **AND** no DB migration is generated for this change (the rename is
  purely textual; the integer column keeps its identifier)

### Requirement: Integrated Search UI with Live Counter
The search filters on the Landing and Dashboard MUST be rendered as searchable dropdowns with the match counter placed in close visual proximity.
- The `combobox.js` widget MUST be used for both "Area" and "Location" inputs.
- The company counter MUST update automatically (debounced) when a filter selection changes.
- In the Landing Hero, the counter MUST be positioned "next to" the filter inputs (e.g., in the same horizontal row or immediate vicinity) to emphasize the interactive nature of the search.

#### Scenario: Selection update triggers counter
- **GIVEN** a user on the landing page.
- **WHEN** the user selects "Software" from the Sector dropdown.
- **THEN** the company counter MUST update to reflect only companies in the "Software" sector.

### Requirement: Restricted Admin User Filters
The Django Admin for the `User` model MUST restrict filter selections to the managed taxonomy.
- The `area_filter` and `location_filter` fields in `UserAdmin` MUST use dropdown (Select) widgets.
- Staff users MUST NOT be able to enter free-text values into these fields.

#### Scenario: Staff edits user filters
- **GIVEN** a staff user in the Django Admin editing a User.
- **WHEN** the staff user opens the "FastJob" fieldset.
- **THEN** they MUST see dropdown menus for "Area filter" and "Location filter" populated from the managed taxonomy.

