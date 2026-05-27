# dashboard Specification

## Purpose
TBD - created by archiving change add-company-filter-finder. Update Purpose after archive.
## Requirements
### Requirement: Search Filters Use DB-Backed Dropdowns
The dashboard "Sector / Área" and "Ubicación" inputs SHALL be searchable dropdowns whose option lists are sourced exclusively from the distinct values of `Company.area` and `Company.location` in the database. Users MUST NOT be able to persist a filter value that is not currently present in the allowed-options whitelist. An empty selection MUST mean "no filter on that field". The dropdowns MUST support multiple selections.

Each combobox dropdown SHALL always render a **per-field "no filter" first option** as the first row, regardless of selection state. The label MUST be:
- Area combobox (`data-combobox="area"`): **"— TODOS LOS SECTORES —"**
- Location combobox (`data-combobox="location"`): **"— TODAS LAS UBICACIONES —"**

Clicking this row MUST clear all selected pills for that combobox. The previous conditional "— Limpiar todos —" row (shown only when `selected.length > 0`) MUST be removed.

#### Scenario: User cannot persist a free-text value
- **GIVEN** the current allowed-options list for `area` does NOT contain the value `"Pesca"`
- **WHEN** the user submits the filter form with `area_filter=Pesca` (e.g. via a hand-crafted POST)
- **THEN** the server rejects the submission with an error message
- **AND** the user's stored `area_filters` remains unchanged

#### Scenario: Empty selection clears the filter
- **WHEN** the user submits the filter form with no `area_filter` payload
- **THEN** the user's stored `area_filters` is cleared
- **AND** the mailing engine treats the user as having no `area` filter

#### Scenario: "No filter" option clears pills, search text, and form inputs
- **GIVEN** a user on the dashboard has selected "Tecnología" and "Diseño" in the sector dropdown and has typed "dis" in the search input
- **WHEN** the user clicks the "— TODOS LOS SECTORES —" row
- **THEN** both sector pills are removed
- **AND** the search input is cleared (`textInput.value` becomes `""`)
- **AND** no hidden `area_filter` inputs remain in the form
- **AND** clicking "Actualizar búsqueda" submits an empty `area_filter` list (equivalent to clearing the filter)

### Requirement: Live Company-Match Counter on Dashboard
The dashboard SHALL display a live counter, immediately below the filter form, showing the number of companies that match the currently-selected filter values. The counter MUST update whenever either dropdown value changes, MUST display only an integer (no company names, emails, or row data), and MUST source its number from the public count endpoint (so engine and counter cannot drift).

#### Scenario: Counter agrees with the mailing engine
- **GIVEN** a user has set `area_filters=["Tecnología", "Diseño"]` and `location_filters=["Madrid"]`
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
The "Subir CV" form's `<input type="file">` SHALL be hidden visually (`class="sr-only"` while remaining keyboard-accessible) and presented through a styled `<label>` that visually matches the rest of the design system (brand button styling). The label's visible text SHALL read `Subir CV (PDF)` to communicate that selecting a file performs the upload (there is no separate submit button — see "CV upload begins automatically on file selection"). A sibling `<span data-filename>` SHALL display the currently selected filename in Spanish (`Sin archivo seleccionado` when empty, otherwise the selected filename). The native browser-rendered `Choose File / No file chosen` text MUST NOT appear anywhere on the page. The form MUST NOT contain any `<button type="submit">`.

#### Scenario: Initial state shows the Spanish placeholder
- **GIVEN** a logged-in user opens the dashboard
- **WHEN** the page first renders
- **THEN** the file-input control's visible label reads `Subir CV (PDF)` and is the only visible control in the upload form
- **AND** the sibling filename span reads exactly `Sin archivo seleccionado`
- **AND** the rendered HTML contains no occurrence of the strings `Choose File` or `No file chosen` (verified via locale-independent test)
- **AND** the rendered HTML contains no `<button type="submit">` inside the upload form
- **AND** the rendered HTML contains no `<input type="text" name="name">` inside the upload form

#### Scenario: After selecting a file, the filename appears
- **GIVEN** the dashboard is rendered and the user clicks the styled label
- **WHEN** the user picks `mi-cv.pdf` in the OS file picker
- **THEN** the filename span updates to `mi-cv.pdf`
- **AND** the underlying `<input type="file">` retains the selected file

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
The authenticated dashboard surface SHALL use the noun `envío` / `envíos` (singular / plural) in every user-visible string — including the global navbar chip in `templates/base.html`, the stat-card heading in `templates/dashboard/index.html`, and any flash message emitted by `apps/dashboard/views.py` — and MUST NOT render the literal substring `crédito` / `créditos` (any case, with or without the acute accent) in the dashboard's HTML or in queued messages-framework text. The numeric value displayed next to the noun MUST be sourced from `User.visible_credits` (which clamps negative values to zero).

#### Scenario: Authenticated navbar chip shows "envíos"
- **GIVEN** an authenticated user with `credits_remaining = 7`
- **WHEN** any page extending `base.html` is rendered for that user
- **THEN** the navbar chip renders the text `7 envíos`
- **AND** the chip does NOT contain the substring `créditos`

#### Scenario: Dashboard stat card heading is "Envíos disponibles"
- **GIVEN** an authenticated user opens `GET /dashboard/`
- **WHEN** the stat-card row at the top of the dashboard is rendered
- **THEN** the card label above the integer reads `Envíos disponibles`
- **AND** the rendered HTML contains no occurrence of the regex `[Cc]r[ée]dito`

#### Scenario: Negative balance shows as 0 in UI
- **GIVEN** an authenticated user with `credits_remaining = -2`
- **WHEN** the dashboard page is rendered
- **THEN** the stat-card shows `0 envíos`

#### Scenario: "No credits" flash message uses "envíos"
- **GIVEN** an authenticated user with `credits_remaining = 0`, a linked OAuth provider, and an active CV
- **WHEN** the user submits `POST /dashboard/toggle-campaign/` with `action=start`
- **THEN** a Django messages-framework `error` is queued whose body is `"No tienes envíos disponibles. Compra un paquete para continuar."`
- **AND** no other queued message text references the word "crédito"

### Requirement: Integrated Search UI with Live Counter
The search filters on the Landing and Dashboard MUST be rendered as searchable dropdowns with the match counter placed in close visual proximity.

- The `combobox.js` widget MUST be used for both "Area" and "Location" inputs.
- The company counter MUST update automatically (debounced) when a filter selection changes, including when the "no filter" option is clicked.
- In the Landing Hero, the counter MUST be positioned "next to" the filter inputs (e.g., in the same horizontal row or immediate vicinity) to emphasize the interactive nature of the search.
- The widget MUST treat a non-OK HTTP response (e.g. `429`, `5xx`) from the option-list endpoint as a failure: it MUST check the response status before parsing the body and MUST NOT initialise the dropdowns with empty option lists on failure.
- The widget MUST NOT memoise a failed option-list fetch; a subsequent trigger MUST be able to retry the request.
- On an option-list fetch failure the widget MUST surface a visible, recoverable error (a message plus a retry control) within the filter UI, on both the Landing page and the Dashboard.
- Each combobox dropdown MUST always render a per-field "no filter" first option ("— TODOS LOS SECTORES —" for area, "— TODAS LAS UBICACIONES —" for location). Clicking this option MUST clear all selected pills for that combobox and debounce a counter update.

After any filter selection change, the widget MUST dynamically update the available options in both comboboxes by fetching `GET /api/companies/available-filters/` with the current selection. The fetched available options replace the dropdown selectable-option lists. Currently-selected pills that fall outside the available options for their dimension MUST remain visible and removable so the user can deselect dead-end values. The dropdown selectable-option list for each combobox MUST only show values from the available-filters response (plus any selected-but-unavailable values for the current combobox, shown as pills only).

When the available-filters fetch fails, the widget MUST keep the previous option lists intact (not empty them) and continue showing the counter. The count endpoint request is independent and MUST still fire.

#### Scenario: Selection update triggers counter and available-filters update
- **GIVEN** a user on the landing page
- **WHEN** the user selects "tecnología" from the Sector dropdown
- **THEN** the company counter MUST update to reflect only companies in tecnología
- **AND** the Location dropdown MUST update to show only locations that have tecnología companies
- **AND** the Area dropdown MUST show all areas (since no location is selected)

#### Scenario: Both dimensions constrain each other
- **GIVEN** a user on the dashboard has selected `area = "tecnología"` and then selects `location = "madrid"`
- **WHEN** the available-filters response arrives
- **THEN** the Area dropdown shows only areas that have companies in Madrid
- **AND** the Location dropdown shows only locations that have tecnología companies
- **AND** the counter reflects the count for tecnología + Madrid

#### Scenario: Selected pill remains removable even when not in available options
- **GIVEN** a user has selected `area = "abogados familiares"` and then selects `location = "valencia"`
- **AND** there are no companies matching "abogados familiares" in "valencia"
- **WHEN** the available-filters response arrives showing that "abogados familiares" is not among the available areas for Valencia
- **THEN** the "ABOGADOS FAMILIARES" pill is still visible in the area combobox
- **AND** the user can click the × on the pill to remove it
- **AND** the Area dropdown does NOT show "abogados familiares" as a selectable option (it appears only as a removable pill)

#### Scenario: Available-filters fetch failure preserves previous options
- **GIVEN** a user has selected `area = "tecnología"` and the available-filters endpoint returns a 500 error
- **WHEN** the response fails
- **THEN** both dropdown option lists remain unchanged (showing the options from the last successful response or the full taxonomy from initial load)
- **AND** the company counter still updates from the count endpoint
- **AND** no dropdowns become empty or non-functional

#### Scenario: Clicking "no filter" clears selections and restores full options
- **GIVEN** a user has selected `area = "tecnología"` and the Location dropdown has been constrained to show only locations with tecnología companies
- **WHEN** the user clicks "— TODOS LOS SECTORES —"
- **THEN** the área pills are cleared
- **AND** the available-filters fetch is triggered with no area filter
- **AND** the Location dropdown is restored to show all locations
- **AND** the Area dropdown shows all areas

#### Scenario: Selection update triggers counter
- **GIVEN** a visitor on the landing page has not selected any filters
- **WHEN** the visitor selects "Tecnología" from the area dropdown
- **THEN** the counter updates to reflect the number of companies matching "Tecnología"

#### Scenario: Clicking "no filter" triggers counter update
- **GIVEN** a visitor has selected "Tecnología" and the counter displays the matching count
- **WHEN** the visitor clicks "— TODOS LOS SECTORES —"
- **THEN** the counter updates to reflect the total number of companies (no filter)

#### Scenario: Option-list fetch failure is visible and retryable
- **GIVEN** the option-list endpoint returns a non-OK response (e.g. `429 Too Many Requests`) when the filter UI loads
- **WHEN** `combobox.js` initialises the Area and Location widgets
- **THEN** the widgets do NOT render as silently empty, non-functional dropdowns
- **AND** a visible error message with a retry control is shown in the filter UI
- **AND** activating the retry control re-requests the option list

#### Scenario: Retry after a transient failure recovers the widget
- **GIVEN** the first option-list fetch failed and the widget is showing the error state
- **WHEN** the option-list endpoint subsequently returns a successful response and the user activates the retry control
- **THEN** the widget re-fetches, populates both dropdowns, and becomes fully functional
- **AND** no page reload is required

#### Scenario: Counter agrees with the mailing engine
- **GIVEN** a user has set `area_filters=["Tecnología", "Diseño"]` and `location_filters=["Madrid"]`
- **AND** the dashboard counter reads `0`
- **WHEN** the slow-drip task runs for that user
- **THEN** the engine sends nothing for that user (because the eligible-company queryset is empty by the same matching rules)

### Requirement: Restricted Admin User Filters
The Django Admin for the `User` model MUST restrict filter selections to the managed taxonomy.
- The `area_filters` and `location_filters` fields in `UserAdmin` MUST use `filter_horizontal` widgets.
- Staff users MUST NOT be able to enter free-text values into these fields.

#### Scenario: Staff edits user filters
- **GIVEN** a staff user in the Django Admin editing a User.
- **WHEN** the staff user opens the "FastJob" fieldset.
- **THEN** they MUST see multi-select widget (filter_horizontal) for "Area filters" and "Location filters" populated from the managed taxonomy.

### Requirement: Dashboard restyle preserves existing layout and toggle pattern
`templates/dashboard/index.html` SHALL retain its current responsive structure:

- a header row containing the page title and the **campaign toggle** (the toggle stays inline in the header, not in a column),
- a stats grid of four cards (`grid sm:grid-cols-2 lg:grid-cols-4`) immediately below the header,
- a content grid `grid lg:grid-cols-3` with a left rail at `lg:col-span-1` (CV list + upload form + Filters + Danger Zone) and a right area at `lg:col-span-2` (Recent Activity table).

The rebrand is a **restyle in place**. The activity table's `min-w-[640px]` MUST be preserved so its four columns stay readable; reflowing it into a narrower column would force horizontal scroll, contradicting the `ui-shell` no-overflow invariant.

Every panel's chrome MUST migrate to the brand tokens: `border-gray-100` → `border-brand-muted`, while keeping `bg-white`, `rounded-2xl`, and `shadow-sm`. Section titles (currently `font-bold text-lg`) MUST adopt `text-h2 text-brand-dark`. The "Actualizar búsqueda" submit button (currently `bg-gray-900 hover:bg-black`) MUST be replaced with `bg-brand hover:bg-brand-dark text-white`. The stats card's primary numeric (`text-brand`) remains, now resolving to the new Vibrant Blue.

#### Scenario: Dashboard layout structure is unchanged
- **GIVEN** a logged-in user at viewport 1280 × 800
- **WHEN** they load `/dashboard/`
- **THEN** the header row contains the page title on the left and the campaign-toggle form on the right
- **AND** below the header, a 4-card stats grid renders in `lg:grid-cols-4`
- **AND** below the stats, a content grid renders with `lg:grid-cols-3`, where CVs + Filters + Danger Zone sit in `lg:col-span-1` and Recent Activity sits in `lg:col-span-2`

#### Scenario: Panel chrome migrates to brand tokens without reflow
- **WHEN** the dashboard renders post-change
- **THEN** every panel's border class resolves to `brand.muted` (not `gray-100`)
- **AND** every section title uses `text-h2` size and `brand.dark` color
- **AND** the "Actualizar búsqueda" submit button's background resolves to `brand.DEFAULT` and on hover to `brand.dark`
- **AND** the `min-w-[640px]` constraint on the recent-activity `<table>` is unchanged

### Requirement: Campaign toggle preserves semantic start/stop colors
The campaign on/off control on the dashboard SHALL retain its current **two-button pattern** in the header row (one rendered when the campaign is active, the other when it is inactive). The "Pausar campaña" button MUST keep its red treatment (`bg-red-500 hover:bg-red-600 text-white`) and the "Iniciar campaña" button MUST keep its green treatment (`bg-green-500 hover:bg-green-600 text-white`); red and green encode stop/start affordance universally and are explicitly permitted by the `ui-shell` "Centralized Brand Identity" exception for semantic status colors.

The rebrand SHALL only add brand-coherent **focus styling** to both buttons (`focus:outline-none focus:ring-2 focus:ring-brand-ring focus:ring-offset-2`) so keyboard users see the brand's focus signal. The pattern MUST NOT be replaced by a unified switch / toggle component, and the buttons MUST NOT be re-skinned in `brand.*` palette colors.

#### Scenario: Active campaign renders the red "Pausar campaña" button
- **GIVEN** a user with `is_campaign_active == True` on `/dashboard/`
- **WHEN** the page renders
- **THEN** the header right side shows a `<button>` with classes resolving to `bg-red-500` and `hover:bg-red-600`
- **AND** its label is `Pausar campaña`
- **AND** the button additionally carries `focus:ring-2 focus:ring-brand-ring focus:ring-offset-2`

#### Scenario: Inactive campaign renders the green "Iniciar campaña" button
- **GIVEN** a user with `is_campaign_active == False` and a linked provider on `/dashboard/`
- **WHEN** the page renders
- **THEN** the header right side shows a `<button>` with classes resolving to `bg-green-500` and `hover:bg-green-600`
- **AND** its label is `Iniciar campaña`
- **AND** the button additionally carries the brand focus-ring utility set

### Requirement: Unified form-control styling on dashboard inputs
Every `<input>`, `<select>`, and `<textarea>` on `templates/dashboard/index.html` and `templates/dashboard/delete_account.html` SHALL share the same visual treatment: `bg-white border border-brand-muted rounded-lg px-3 py-2 text-brand-ink focus:outline-none focus:ring-2 focus:ring-brand-ring focus:border-brand`. The combobox widgets (`data-combobox="area"` / `"location"`) MUST adopt the same focused appearance via their existing JavaScript controller (no behavior change to the controller itself).

#### Scenario: All dashboard inputs share the same focus ring
- **GIVEN** a logged-in user on `/dashboard/`
- **WHEN** they Tab through every form field, including the combobox widgets and any input on the delete-account page
- **THEN** each focused field renders an outline using `brand.ring` and a `brand.DEFAULT` border color
- **AND** no field exhibits a different focus color or border treatment

### Requirement: Filter option labels display in uppercase on Dashboard
The authenticated dashboard filter widgets (Sector/Área and Ubicación) SHALL display all option labels in UPPERCASE — both inside the dropdown list and inside the selected-value pills. The underlying values submitted to the server for persisting user preferences MUST remain unchanged (lowercase, as stored in the database). The visual transformation MUST be achieved via CSS (`text-transform: uppercase`) so that hidden input values, server-side whitelist validation, and the mailing engine matching logic are unaffected.

The "no filter" first row ("— TODOS LOS SECTORES —" / "— TODAS LAS UBICACIONES —") MUST also appear in uppercase and MUST be subject to the same CSS `text-transform: uppercase` rule.

#### Scenario: Dropdown option labels appear in uppercase on Dashboard
- **GIVEN** the database contains locations `{"madrid", "barcelona"}`
- **WHEN** an authenticated user opens the Ubicación dropdown on the dashboard
- **THEN** the dropdown list renders the labels as `MADRID` and `BARCELONA`
- **AND** the "no filter" row renders as `— TODAS LAS UBICACIONES —`
- **AND** the POST request to `/filtros/` still sends the lowercase values `madrid` and `barcelona`

#### Scenario: Selected pill labels appear in uppercase on Dashboard
- **GIVEN** the user has `location_filters = ["madrid"]` saved
- **WHEN** the dashboard page loads and pre-fills the combobox from `data-value`
- **THEN** the pill inside the Ubicación combobox renders `MADRID`
- **AND** the hidden form input value for that selection remains `madrid`

#### Scenario: Backend validation is unaffected by uppercase display
- **GIVEN** the current allowed-options list for `area` contains `"tecnología"` (lowercase)
- **WHEN** the user submits the filter form after selecting the option displayed as `TECNOLOGÍA`
- **THEN** the server accepts the submission (hidden input value is `tecnología`, which matches
  the whitelist)
- **AND** the user's `area_filters` is updated to `["tecnología"]`

### Requirement: CV upload begins automatically on file selection
Selecting a file via the `#cv-file-input` element on `/dashboard/` SHALL begin the upload immediately, without any further user action. The form MUST NOT expose a submit button. Client-side validation (extension `.pdf` case-insensitive, size ≤ 10 MB) SHALL run before any network request, and on failure SHALL surface an inline Spanish error in a sibling `<p data-upload-status>` element, reset `input.value = ""` so the same file can be re-picked, and not contact the server. On a valid selection, the page SHALL POST `multipart/form-data` (containing `cv_file` and `csrfmiddlewaretoken`) to the existing `{% url 'upload_cv' %}` endpoint with header `X-Requested-With: XMLHttpRequest`, display the status message `Subiendo…`, and disable the upload label while the request is in flight. On HTTP `200`, the page SHALL fully reload so the server re-renders the CV list, the "Activo" highlight, and Django flash messages from the canonical view. On a non-`2xx` response, the JSON `error` string SHALL be displayed inline in red, the label re-enabled, and `input.value` reset so the user can retry. The `upload_cv` view SHALL continue to accept ordinary (non-AJAX) form posts and respond with the existing redirect + flash-message behavior, so the feature degrades gracefully when JavaScript is disabled.

#### Scenario: Valid PDF triggers upload without an extra click
- **GIVEN** a logged-in user on `/dashboard/`
- **WHEN** they pick `mi-cv.pdf` (≤ 10 MB) in the OS file picker
- **THEN** no submit button click is required
- **AND** the inline status region reads `Subiendo…` while the request is in flight
- **AND** the browser issues exactly one POST to `/dashboard/subir-cv/` with header `X-Requested-With: XMLHttpRequest` containing `cv_file` and `csrfmiddlewaretoken`
- **AND** on `200 {"ok": true}` the page reloads, the new CV appears in "Tus CVs" marked as active, and the green Django success toast `CV subido correctamente.` is shown

#### Scenario: Wrong file type is rejected client-side with no network request
- **GIVEN** a logged-in user on `/dashboard/`
- **WHEN** they pick a `.txt` file in the OS file picker
- **THEN** the inline status region shows `Solo se permiten archivos PDF.` in red
- **AND** no network request is issued
- **AND** the file input value is cleared so the user can immediately pick another file (including the same one again)

#### Scenario: Oversize PDF is rejected client-side with no network request
- **GIVEN** a logged-in user on `/dashboard/`
- **WHEN** they pick a PDF larger than 10 MB
- **THEN** the inline status region shows `El archivo no puede superar los 10 MB.` in red
- **AND** no network request is issued
- **AND** the file input value is cleared

#### Scenario: Server-side validation failure surfaces inline
- **GIVEN** a logged-in user on `/dashboard/` whose client-side checks pass
- **WHEN** the AJAX request returns `400 {"ok": false, "error": "Por favor selecciona un archivo PDF."}`
- **THEN** the inline status region displays exactly that Spanish error in red
- **AND** the upload label is re-enabled
- **AND** the file input value is cleared so the user can retry
- **AND** the page does NOT reload

#### Scenario: Non-AJAX submission still works (no-JS fallback)
- **GIVEN** a client without JavaScript (or any client omitting the `X-Requested-With` header)
- **WHEN** they POST a valid PDF to `/dashboard/subir-cv/` with a valid CSRF token
- **THEN** the response is a `302` redirect to `/dashboard/`
- **AND** the next page render includes the Django success flash message `CV subido correctamente.`
- **AND** the new CV is created and set as the user's active CV

### Requirement: CV Deletion Blocked During Active Campaign

The `delete_cv` view and the dashboard template SHALL prevent a user from deleting any CV while their campaign is active. This is a server-side guard with a template-level visual hint for defence in depth.

#### Scenario: Server rejects deletion when campaign is active

- **GIVEN** a logged-in user whose `is_campaign_active` is `True`
- **WHEN** they submit `POST /dashboard/cv/<cv_id>/eliminar/` for any of their CVs
- **THEN** the view returns a redirect to the dashboard with an error flash message reading `"Para eliminar un CV, primero pausa tu campaña."`
- **AND** the CV row is NOT deleted from the database
- **AND** the S3 file is NOT removed
- **AND** `user.is_campaign_active` remains `True`
- **AND** `user.active_cv` is unchanged

#### Scenario: Server allows deletion when campaign is paused

- **GIVEN** a logged-in user whose `is_campaign_active` is `False`
- **WHEN** they submit `POST /dashboard/cv/<cv_id>/eliminar/`
- **THEN** the CV is deleted (row + S3 file per `pre_delete` signal)
- **AND** the existing fallback logic applies (switch `active_cv` to the most recent remaining CV, or pause if none)

#### Scenario: Delete button hidden in template when campaign is active

- **GIVEN** a logged-in user whose `is_campaign_active` is `True`
- **WHEN** the dashboard page is rendered
- **THEN** no "Eliminar" button is visible on any CV row in "Tus CVs"

#### Scenario: Delete button visible when campaign is paused

- **GIVEN** a logged-in user whose `is_campaign_active` is `False`
- **WHEN** the dashboard page is rendered
- **THEN** every CV row shows an "Eliminar" button (including the active CV, since deletion is always allowed when the campaign is paused — the existing fallback logic handles `active_cv` reassignment)

### Requirement: Search-suggestion animation in the dashboard filters
The dashboard "Filtros de busqueda" section (`templates/dashboard/index.html`) SHALL render a typewriter-animated suggestion element (`<span data-search-suggestion>`) immediately below the section heading (`<h2>`) and the company counter chip, inside the existing heading container, positioned above the filter form. The element SHALL display cycling strings in the format `"{Area} en {Location}..."` using the same Typed.js animation and `search-suggestion.js` module as the landing page.

The suggestion element on the dashboard SHALL:
- Use the same visual styling as the landing page (`text-brand`, `hover:text-brand-dark`, `cursor-pointer`, `transition`)
- Carry `aria-hidden="true"`
- Pause when any combobox input within the same `[data-filter-widget]` receives focus, and resume when all combobox inputs lose focus
- Respect `prefers-reduced-motion: reduce` with a static fallback (identical behaviour to the landing page)

When the user clicks the suggestion on the dashboard:
- The area and location comboboxes SHALL be pre-filled with the parsed values
- The form SHALL NOT be auto-submitted (the user must click "Actualizar busqueda")
- The company counter SHALL update immediately (triggered by the combobox's existing `onChange` callback)

If the filter-options response contains fewer than 2 areas or fewer than 2 locations, the element SHALL display the static fallback text `"Busca por sector y ubicación"`.

#### Scenario: Animated suggestion renders under the dashboard heading
- **GIVEN** an authenticated user on `/dashboard/`
- **WHEN** the filters section renders
- **THEN** a `<span data-search-suggestion>` element appears below the `"Filtros de busqueda"` heading and counter chip, above the filter form
- **AND** the element displays a typewriter-animated string in the format `"{Area} en {Location}..."`

#### Scenario: Clicking the suggestion pre-fills dashboard comboboxes without submitting
- **GIVEN** the animated suggestion currently displays `"Tecnologia en Barcelona..."`
- **AND** `"tecnologia"` and `"barcelona"` are valid values in the whitelist
- **WHEN** the user clicks the suggestion element
- **THEN** the area combobox gains the value `"tecnologia"` and the location combobox gains the value `"barcelona"`
- **AND** the company counter updates immediately
- **AND** the form is NOT submitted (the user must click "Actualizar busqueda" to persist the filters)

#### Scenario: Animation pauses while a dashboard combobox is focused
- **GIVEN** the suggestion animation is cycling on the dashboard
- **WHEN** the user focuses either the area or location combobox input
- **THEN** the animation pauses
- **WHEN** the user blurs both combobox inputs
- **THEN** the animation resumes

#### Scenario: Reduced-motion user sees a static suggestion on the dashboard
- **GIVEN** a dashboard user with `prefers-reduced-motion: reduce`
- **WHEN** the dashboard renders
- **THEN** the `<span data-search-suggestion>` displays a single static suggestion string
- **AND** no animation or cursor is visible

