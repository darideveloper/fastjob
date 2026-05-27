## MODIFIED Requirements

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