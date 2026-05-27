## MODIFIED Requirements

### Requirement: Public Company-Finder Section on Landing Page
The public landing page SHALL include a section, positioned **immediately below the hero section**, that lets anonymous visitors explore the company database by sector and location. The section MUST be 100% functional without authentication. It MUST consist of two searchable dropdown widgets (sector and location) and a live counter showing the number of matching companies. The widgets' option lists MUST be sourced from the same allowed-options whitelist as the dashboard. The counter MUST display only an integer and MUST NOT expose any company name, email, primary key, or other row-level data anywhere in the rendered HTML or JavaScript.

After any filter selection change, the widget MUST dynamically update the available options in both comboboxes by fetching `GET /api/companies/available-filters/` with the current selection. The fetched available options replace the dropdown selectable-option lists. Currently-selected pills that are no longer in the available options MUST remain visible and removable so the user can deselect dead-end values. The dropdown list MUST only show options from the available-filters response (plus any selected-but-unavailable values shown as pills, not as selectable rows).

When the section's backing API requests fail (rate limit `429`, server error, or network failure), the section MUST degrade gracefully and visibly: it MUST NOT silently render empty, non-functional dropdowns. The visitor MUST be shown a recoverable error state with a retry affordance.

Each combobox dropdown SHALL always render a **per-field "no filter" first option** as the first row, regardless of selection state. The label MUST be:
- Area combobox (`data-combobox="area"`): **"— TODOS LOS SECTORES —"**
- Location combobox (`data-combobox="location"`): **"— TODAS LAS UBICACIONES —"**

Clicking this row MUST clear all selected pills for that combobox, trigger both a counter update and an available-filters update.

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

#### Scenario: Cascading options update on the landing page after selection
- **GIVEN** a visitor on the landing page has selected `area="tecnología"`
- **WHEN** the available-filters response arrives
- **THEN** the Location dropdown updates to show only locations that have tecnología companies
- **AND** the Area dropdown shows all areas (since no location is selected)

#### Scenario: Selected pill remains removable even when not in available options
- **GIVEN** a visitor has selected `area="abogados familiares"` and then selects `location="valencia"`
- **AND** there are no companies matching "abogados familiares" in "valencia"
- **WHEN** the available-filters response arrives showing that "abogados familiares" is not among the available areas for Valencia
- **THEN** the "ABOGADOS FAMILIARES" pill is still visible in the area combobox
- **AND** the visitor can click the × on the pill to remove it
- **AND** the Area dropdown does NOT show "abogados familiares" as a selectable option

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

#### Scenario: Available-filters fetch failure preserves previous options
- **GIVEN** a visitor has selected `area="tecnología"` and the available-filters endpoint returns a 500 error
- **WHEN** the response fails
- **THEN** both dropdown option lists remain unchanged (showing the options from the last successful response or the full taxonomy from initial load)
- **AND** the company counter still updates from the count endpoint
- **AND** no dropdowns become empty or non-functional

#### Scenario: Clicking "no filter" clears selections and restores full options
- **GIVEN** a visitor has selected `area="tecnología"` and the Location dropdown has been constrained to show only locations with tecnología companies
- **WHEN** the visitor clicks "— TODOS LOS SECTORES —"
- **THEN** the área pills are cleared
- **AND** the available-filters fetch is triggered with no area filter
- **AND** the Location dropdown is restored to show all locations
- **AND** the Area dropdown shows all areas