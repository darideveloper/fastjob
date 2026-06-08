## MODIFIED Requirements

### Requirement: Public Company-Finder Section on Landing Page
The public landing page SHALL include a section, positioned **immediately below the hero section**, that lets anonymous visitors explore the company database by sector, sub-activity, and location. The section MUST consist of three searchable dropdown widgets (sector, sub-activity, and location) and a live counter showing the number of matching companies.

#### Scenario: Anonymous visitor sees the section with three dropdowns
- **WHEN** they load the landing page
- **THEN** the company-finder section contains three combobox widgets: Sector, Subactividad, and Ubicación.
- **AND** the widgets are populated with whitelist values from the database.

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
