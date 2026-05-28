## ADDED Requirements

### Requirement: Combobox input loses focus after selecting a filter option on the dashboard

When the user selects an option from either the area or location combobox dropdown on the dashboard (including the "— TODOS LOS SECTORES —" / "— TODAS LAS UBICACIONES —" clear row), the combobox text input MUST lose focus (blur). This ensures:

- The blinking cursor disappears (no ambiguous "cursor with no dropdown" state)
- The dropdown stays closed until the user explicitly interacts with the control again
- When the user clicks the control wrapper or the input, the existing `focus` event handler re-opens the dropdown with fully refreshed options (excluding already-selected values)

The blur MUST be triggered imperatively via `textInput.blur()` inside the `mousedown` event handler, after the selection has been processed and the dropdown has been hidden. The existing `e.preventDefault()` call in the `mousedown` handler MUST be preserved so the input does not lose focus to the browser's default mousedown behavior before the imperative blur takes effect.

Keyboard selection (Enter key on a highlighted item) MUST produce the same result: after the synthetic `mousedown` event is dispatched and handled, the input MUST lose focus.

The filter form submission ("Actualizar búsqueda") MUST be unaffected: the user can still click the submit button after selecting filters, regardless of the input blur state.

#### Scenario: Selecting a filter option removes cursor and closes dropdown

- **GIVEN** an authenticated user on the dashboard
- **WHEN** they open the area combobox dropdown and click `TECNOLOGÍA`
- **THEN** the `TECNOLOGÍA` pill is added to the combobox
- **AND** the dropdown closes
- **AND** the text input loses focus (no blinking cursor)
- **AND** `document.activeElement` is NOT the combobox text input

#### Scenario: Clicking "clear all" removes cursor and closes dropdown

- **GIVEN** an authenticated user on the dashboard with `TECNOLOGÍA` selected
- **WHEN** they open the area combobox dropdown and click `— TODOS LOS SECTORES —`
- **THEN** the `TECNOLOGÍA` pill is removed
- **AND** the dropdown closes
- **AND** the text input loses focus

#### Scenario: Filter form submission unaffected by blur

- **GIVEN** an authenticated user on the dashboard with `TECNOLOGÍA` selected and the input blurred
- **WHEN** they click "Actualizar búsqueda"
- **THEN** the form submits successfully with the selected `area_filter` value
- **AND** the filter persists after page reload

#### Scenario: Keyboard Enter selection also blurs the input

- **GIVEN** an authenticated user on the dashboard with keyboard focus on the area combobox
- **WHEN** they press ArrowDown to highlight the first option and press Enter
- **THEN** the option is selected and the text input loses focus (same behavior as mouse click)
