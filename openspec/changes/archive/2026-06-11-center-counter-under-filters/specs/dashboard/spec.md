## MODIFIED Requirements

### Requirement: Live Company-Match Counter on Dashboard
The dashboard SHALL display a live counter, positioned above the filter inputs and centered horizontally, showing the number of companies that match the currently-selected filter values. The counter MUST update whenever either dropdown value changes, MUST display only an integer (no company names, emails, or row data), and MUST source its number from the public count endpoint (so engine and counter cannot drift).

#### Scenario: Counter agrees with the mailing engine
- **GIVEN** a user has set `area_filters=["Tecnología", "Diseño"]` and `location_filters=["Madrid"]`
- **AND** the dashboard counter reads `0`
- **WHEN** the slow-drip task runs for that user
- **THEN** the engine sends nothing for that user (because the eligible-company queryset is empty by the same matching rules)

### Requirement: Search-suggestion animation in the dashboard filters
The dashboard "Filtros de busqueda" section (`templates/dashboard/index.html`) SHALL render a typewriter-animated suggestion element (`<span data-search-suggestion>`) immediately below the section heading (`<h2>`), positioned above the filter form. The element SHALL display cycling strings in the format `"{Area} en {Location}..."` using the same Typed.js animation and `search-suggestion.js` module as the landing page.

#### Scenario: Animated suggestion renders under the dashboard heading
- **GIVEN** an authenticated user on `/dashboard/`
- **WHEN** the filters section renders
- **THEN** a `<span data-search-suggestion>` element appears below the `"Filtros de busqueda"` heading, above the filter form
- **AND** the element displays a typewriter-animated string in the format `"{Area} en {Location}..."`

#### Scenario: Clicking the suggestion pre-fills dashboard comboboxes without submitting
- **GIVEN** the animated suggestion currently displays `"Tecnologia en Barcelona..."`
- **AND** `"tecnologia"` and `"barcelona"` are valid values in the whitelist
- **WHEN** the user clicks the suggestion element
- **THEN** the area combobox gains the value `"tecnologia"` and the location combobox gains the value `"barcelona"`
- **AND** the company counter updates immediately
- **AND** the form is NOT submitted (the user must click "Actualizar busqueda" to persist the filters)
- **AND** the suggestion element fades out permanently

#### Scenario: Animation pauses while a dashboard combobox is focused
- **GIVEN** the animated suggestion is cycling on the dashboard
- **WHEN** the user focuses the area or location combobox input
- **THEN** the Typed.js instance pauses cycling
- **AND** it resumes cycling when all inputs lose focus (unless already permanently hidden)
