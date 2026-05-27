## MODIFIED Requirements

### Requirement: Search-suggestion animation in the company-finder section
The public landing page company-finder section (`templates/home.html`) SHALL render a typewriter-animated suggestion element (`<span data-search-suggestion>`) immediately below the section subtitle (`<p>`) and above the filter card. The element SHALL display cycling strings in the format `"{Area} en {Location}..."` — for example, `"Abogados en Madrid..."` — where `{Area}` and `{Location}` are real values drawn from the `/api/companies/filter-options/` response. The animation SHALL be powered by the vendored Typed.js library (`static/js/vendor/typed.min.js`), initialised by `static/js/search-suggestion.js`.

The suggestion element SHALL:
- Use `text-brand` colour with `hover:text-brand-dark transition` to signal clickability (the element has `cursor-pointer`)
- Carry `aria-hidden="true"` so screen readers skip the transient animation
- Have a `min-height` equivalent to one line of text (`min-h-[1.25rem]` or equivalent `1.25rem`) so the layout never collapses even if content is briefly empty
- Pause (stop cycling) when any combobox input within the same `[data-filter-widget]` receives focus, and resume when all combobox inputs lose focus — **unless** the suggestion has already been permanently hidden due to user interaction

When a user first interacts with the filter widget (by focusing a combobox input or clicking the suggestion to pre-fill values), the suggestion SHALL fade out permanently with a `0.3s ease` opacity transition. Once hidden, the animation SHALL NOT restart or rebuild. This eliminates visual glitches from destroying and recreating the Typed.js instance on every filter change.

The suggestion SHALL NOT be rebuilt when cascading filter options change. The `rebuildSuggestions()` path triggered by `FastJobFilter.onOptionsChange` SHALL be removed entirely. Suggestions are decorative and generated from the full taxonomy at page-load time; they do not need to reflect the currently-narrowed filter state.

When `prefers-reduced-motion: reduce` is active, the element SHALL render a single static suggestion string (the first string from the shuffled list) with no animation, no cursor, and no Typed.js initialisation. This static string also hides on first user interaction.

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
- **AND** the suggestion element fades out permanently (opacity transitions to 0 over 0.3s)

#### Scenario: Animation pauses while a combobox is focused
- **GIVEN** the suggestion animation is actively cycling and has not been permanently hidden
- **WHEN** the visitor clicks into (or tabs into) either the area or location combobox input
- **THEN** the typing animation pauses (no further string transitions)

#### Scenario: Suggestion hides permanently on first filter interaction
- **GIVEN** the suggestion animation is actively cycling
- **WHEN** the visitor focuses either the area or location combobox input
- **THEN** the suggestion element fades out with a `0.3s ease` opacity transition
- **AND** the Typed.js instance is destroyed
- **AND** the suggestion element's innerHTML is cleared
- **AND** subsequent focus/blur cycles on the combobox inputs do NOT restart the animation

#### Scenario: No suggestion rebuild on filter change
- **GIVEN** the visitor has not yet interacted with the filter widget (suggestion is still visible)
- **WHEN** the available-filters API response updates the combobox option lists
- **THEN** the suggestion animation continues uninterrupted (no destroy+recreate cycle)
- **AND** there is no layout jump or vertical shift in the filter section

#### Scenario: Reduced-motion user sees a static suggestion
- **GIVEN** a visitor whose OS reports `prefers-reduced-motion: reduce`
- **WHEN** the landing page renders
- **THEN** the `<span data-search-suggestion>` displays a single static string (the first suggestion from the generated list)
- **AND** no typewriter animation or blinking cursor is visible
- **AND** Typed.js is NOT initialised (to avoid unnecessary JS overhead)
- **AND** the static suggestion also hides on first user interaction (focus or click)

#### Scenario: Fallback hint when too few filter options exist
- **GIVEN** the `/api/companies/filter-options/` response returns fewer than 2 areas or fewer than 2 locations
- **WHEN** the suggestion module initialises
- **THEN** the `<span data-search-suggestion>` displays the static text `"Busca por sector y ubicación"`
- **AND** the element is not interactive (no click handler, no combobox fill)
- **AND** the element has `min-height: 1.25rem` so the layout does not collapse

#### Scenario: Suggestion element is hidden from screen readers
- **GIVEN** a screen-reader user navigating the landing page
- **WHEN** the company-finder section is encountered
- **THEN** the `<span data-search-suggestion>` element has `aria-hidden="true"`
- **AND** the screen reader announces the section heading and the combobox placeholders (which already contain type-to-search hints) but skips the animated suggestion