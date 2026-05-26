## MODIFIED Requirements

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

### Requirement: Integrated Search UI with Live Counter

The search filters on the Landing and Dashboard MUST be rendered as searchable dropdowns with the match counter placed in close visual proximity.

- The `combobox.js` widget MUST be used for both "Area" and "Location" inputs.
- The company counter MUST update automatically (debounced) when a filter selection changes, including when the "no filter" option is clicked.
- In the Landing Hero, the counter MUST be positioned "next to" the filter inputs (e.g., in the same horizontal row or immediate vicinity) to emphasize the interactive nature of the search.
- The widget MUST treat a non-OK HTTP response (e.g. `429`, `5xx`) from the option-list endpoint as a failure: it MUST check the response status before parsing the body and MUST NOT initialise the dropdowns with empty option lists on failure.
- The widget MUST NOT memoise a failed option-list fetch; a subsequent trigger MUST be able to retry the request.
- On an option-list fetch failure the widget MUST surface a visible, recoverable error (a message plus a retry control) within the filter UI, on both the Landing page and the Dashboard.
- Each combobox dropdown MUST always render a per-field "no filter" first option ("— TODOS LOS SECTORES —" for area, "— TODAS LAS UBICACIONES —" for location). Clicking this option MUST clear all selected pills for that combobox and debounce a counter update.

#### Scenario: Selection update triggers counter

- **GIVEN** a user on the landing page.
- **WHEN** the user selects "Software" from the Sector dropdown.
- **THEN** the company counter MUST update to reflect only companies in the "Software" sector.

#### Scenario: Clicking "no filter" triggers counter update

- **GIVEN** a user on the dashboard with "Tecnología" selected in the sector dropdown and a visible company counter
- **WHEN** the user clicks the "— TODOS LOS SECTORES —" row
- **THEN** the "Tecnología" pill is removed
- **AND** the company counter updates to reflect the count without any area filter

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