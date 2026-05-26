## MODIFIED Requirements

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