## MODIFIED Requirements

### Requirement: Search-suggestion animation in the dashboard filters
The dashboard "Filtros de busqueda" section (`templates/dashboard/index.html`) SHALL render a typewriter-animated suggestion element (`<span data-search-suggestion>`) immediately below the section heading (`<h2>`) and the company counter chip, inside the existing heading container, positioned above the filter form. The element SHALL display cycling strings in the format `"{Area} en {Location}..."` using the same Typed.js animation and `search-suggestion.js` module as the landing page.

The suggestion element on the dashboard SHALL:
- Use the same visual styling as the landing page (`text-brand`, `hover:text-brand-dark`, `cursor-pointer`, `transition`)
- Carry `aria-hidden="true"`
- Have a `min-height` equivalent to one line of text (`min-h-[1.25rem]` or equivalent `1.25rem`) so the layout never collapses even if content is briefly empty
- Pause when any combobox input within the same `[data-filter-widget]` receives focus, and resume when all combobox inputs lose focus — **unless** the suggestion has already been permanently hidden due to user interaction
- Respect `prefers-reduced-motion: reduce` with a static fallback (identical behaviour to the landing page)

When a user first interacts with the filter widget (by focusing a combobox input or clicking the suggestion), the suggestion SHALL fade out permanently with a `0.3s ease` opacity transition. Once hidden, the animation SHALL NOT restart or rebuild.

The suggestion SHALL NOT be rebuilt when cascading filter options change. The `rebuildSuggestions()` path triggered by `FastJobFilter.onOptionsChange` SHALL NOT be invoked for the dashboard suggestion element.

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
- **AND** the suggestion element fades out permanently

#### Scenario: Animation pauses while a dashboard combobox is focused
- **GIVEN** the suggestion animation is cycling on the dashboard and has not been permanently hidden
- **WHEN** the user focuses either the area or location combobox input
- **THEN** the animation pauses
- **WHEN** the user blurs both combobox inputs
- **THEN** the animation resumes

#### Scenario: Suggestion hides permanently on first filter interaction on dashboard
- **GIVEN** the suggestion animation is actively cycling on the dashboard
- **WHEN** the user focuses either the area or location combobox input
- **THEN** the suggestion element fades out with a `0.3s ease` opacity transition
- **AND** the Typed.js instance is destroyed
- **AND** subsequent focus/blur cycles do NOT restart the animation

#### Scenario: No suggestion rebuild on dashboard filter change
- **GIVEN** the user has not yet interacted with the dashboard filter widget (suggestion is still visible)
- **WHEN** the available-filters API response updates the combobox option lists
- **THEN** the suggestion animation continues uninterrupted (no destroy+recreate cycle)
- **AND** there is no layout jump or vertical shift in the filter section

#### Scenario: Reduced-motion user sees a static suggestion on the dashboard
- **GIVEN** a dashboard user with `prefers-reduced-motion: reduce`
- **WHEN** the dashboard renders
- **THEN** the `<span data-search-suggestion>` displays a single static suggestion string
- **AND** no animation or cursor is visible
- **AND** the static suggestion also hides on first user interaction