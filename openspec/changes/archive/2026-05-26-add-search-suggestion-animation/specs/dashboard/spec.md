## ADDED Requirements

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