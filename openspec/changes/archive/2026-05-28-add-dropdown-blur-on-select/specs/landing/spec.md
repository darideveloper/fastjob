## ADDED Requirements

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
