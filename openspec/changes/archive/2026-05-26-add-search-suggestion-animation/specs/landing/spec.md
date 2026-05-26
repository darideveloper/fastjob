## ADDED Requirements

### Requirement: Search-suggestion animation in the company-finder section
The public landing page company-finder section (`templates/home.html`) SHALL render a typewriter-animated suggestion element (`<span data-search-suggestion>`) immediately below the section subtitle (`<p>`) and above the filter card. The element SHALL display cycling strings in the format `"{Area} en {Location}..."` — for example, `"Abogados en Madrid..."` — where `{Area}` and `{Location}` are real values drawn from the `/api/companies/filter-options/` response. The animation SHALL be powered by the vendored Typed.js library (`static/js/vendor/typed.min.js`), initialised by `static/js/search-suggestion.js`.

The suggestion element SHALL:
- Use `text-brand` colour with `hover:text-brand-dark transition` to signal clickability (the element has `cursor-pointer`)
- Carry `aria-hidden="true"` so screen readers skip the transient animation
- Pause (stop cycling) when any combobox input within the same `[data-filter-widget]` receives focus, and resume when all combobox inputs lose focus

When `prefers-reduced-motion: reduce` is active, the element SHALL render a single static suggestion string (the first string from the shuffled list) with no animation, no cursor, and no Typed.js initialisation.

The suggestion strings SHALL be generated from 8-12 random combinations of areas and locations from the filter-options response. If the response contains fewer than 2 areas or fewer than 2 locations, the element SHALL fall back to a static hint: `"Busca por sector y ubicación"`.

#### Scenario: Animated suggestion renders under the section heading
- **GIVEN** an anonymous visitor on the home page at viewport 1280 × 800
- **WHEN** the company-finder section renders
- **THEN** a `<span data-search-suggestion>` element appears immediately below the section subtitle `<p>` and above the filter card
- **AND** the element displays a typewriter-animated string in the format `"{Area} en {Location}..."` (e.g. `"Abogados en Madrid..."`)
- **AND** the element's text colour resolves to `brand.DEFAULT` (`#007BFF`)

#### Scenario: Clicking the suggestion pre-fills the comboboxes and updates the count
- **GIVEN** the animated suggestion currently displays `"Abogados en Madrid..."`
- **AND** `"Abogados"` is a valid area in the whitelist
- **AND** `"Madrid"` is a valid location in the whitelist
- **WHEN** the visitor clicks the suggestion element
- **THEN** the area combobox gains the value `"abogados"` (matching the whitelist)
- **AND** the location combobox gains the value `"Madrid"` (matching the whitelist)
- **AND** the company counter updates to reflect the combined filter (triggered by the combobox's existing `onChange` callback)
- **AND** the page does NOT navigate away (the user remains on the landing page)

#### Scenario: Animation pauses while a combobox is focused
- **GIVEN** the suggestion animation is actively cycling
- **WHEN** the visitor clicks into (or tabs into) either the area or location combobox input
- **THEN** the typing animation pauses (no further string transitions)
- **WHEN** the visitor unfocuses (blurs) the combobox input
- **THEN** the animation resumes from where it paused

#### Scenario: Reduced-motion user sees a static suggestion
- **GIVEN** a visitor whose OS reports `prefers-reduced-motion: reduce`
- **WHEN** the landing page renders
- **THEN** the `<span data-search-suggestion>` displays a single static string (the first suggestion from the generated list)
- **AND** no typewriter animation or blinking cursor is visible
- **AND** Typed.js is NOT initialised (to avoid unnecessary JS overhead)

#### Scenario: Fallback hint when too few filter options exist
- **GIVEN** the `/api/companies/filter-options/` response returns fewer than 2 areas or fewer than 2 locations
- **WHEN** the suggestion module initialises
- **THEN** the `<span data-search-suggestion>` displays the static text `"Busca por sector y ubicación"`
- **AND** the element is not interactive (no click handler, no combobox fill)

#### Scenario: Suggestion element is hidden from screen readers
- **GIVEN** a screen-reader user navigating the landing page
- **WHEN** the company-finder section is encountered
- **THEN** the `<span data-search-suggestion>` element has `aria-hidden="true"`
- **AND** the screen reader announces the section heading and the combobox placeholders (which already contain type-to-search hints) but skips the animated suggestion