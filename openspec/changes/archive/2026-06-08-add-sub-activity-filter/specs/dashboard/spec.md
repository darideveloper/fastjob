## MODIFIED Requirements

### Requirement: Search Filters Use DB-Backed Dropdowns
The dashboard "Sector / Área", "Ubicación", and new "Subactividad" inputs SHALL be searchable dropdowns whose option lists are sourced exclusively from the distinct values of `Company.area`, `Company.location`, and `Company.sub_area` in the database. Users MUST NOT be able to persist a filter value that is not currently present in the allowed-options whitelist. An empty selection MUST mean "no filter on that field". The dropdowns MUST support multiple selections.

Each combobox dropdown SHALL always render a **per-field "no filter" first option** as the first row, regardless of selection state. The label MUST be:
- Area combobox (`data-combobox="area"`): **"— TODOS LOS SECTORES —"**
- Location combobox (`data-combobox="location"`): **"— TODAS LAS UBICACIONES —"**
- Sub-Area combobox (`data-combobox="sub_area"`): **"— TODAS LAS SUBACTIVIDADES —"**

Clicking this row MUST clear all selected pills for that combobox.

#### Scenario: User cannot persist a free-text value for sub-area
- **GIVEN** the current allowed-options list for `sub_area` does NOT contain the value `"pesca marina"`
- **WHEN** the user submits the filter form with `sub_area_filter=pesca marina`
- **THEN** the server rejects the submission with an error message
- **AND** the user's stored `sub_area_filters` remains unchanged

### Requirement: Live Company-Match Counter on Dashboard
The dashboard SHALL display a live counter, immediately below the filter form, showing the number of companies that match the currently-selected filter values (including the new sub-area selections). The counter MUST update whenever any dropdown value changes, MUST display only an integer, and MUST source its number from the public count endpoint.

#### Scenario: Counter accounts for selected sub-areas
- **GIVEN** a user has set `sub_area_filters=["productos de limpieza"]`
- **AND** the dashboard counter reads `5`
- **WHEN** the user adds a second sub-area filter
- **THEN** the counter updates live to show the count of companies matching either sub-area (with OR logic)

### Requirement: Filter option labels display in uppercase on Dashboard
The authenticated dashboard filter widgets (Sector/Área, Ubicación, and Subactividad) SHALL display all option labels in UPPERCASE — both inside the dropdown list and inside the selected-value pills. The underlying values submitted to the server for persisting user preferences MUST remain unchanged (lowercase, as stored in the database).

#### Scenario: Sub-area option labels appear in uppercase on Dashboard
- **GIVEN** the database contains sub-areas `{"productos de limpieza", "cosmeticos natural"}`
- **WHEN** an authenticated user opens the Subactividad dropdown on the dashboard
- **THEN** the dropdown list renders the labels as `PRODUCTOS DE LIMPIEZA` and `COSMETICOS NATURAL`
- **AND** the "no filter" row renders as `— TODAS LAS SUBACTIVIDADES —`
- **AND** the POST request still sends the lowercase values

### Requirement: Unified form-control styling on dashboard inputs
Every `<input>`, `<select>`, and `<textarea>` on `templates/dashboard/index.html` and `templates/dashboard/delete_account.html` SHALL share the same visual treatment: `bg-white border border-brand-muted rounded-lg px-3 py-2 text-brand-ink focus:outline-none focus:ring-2 focus:ring-brand-ring focus:border-brand`. The combobox widgets (`data-combobox="area"` / `"location"` / `"sub_area"`) MUST adopt the same focused appearance via their existing JavaScript controller.
