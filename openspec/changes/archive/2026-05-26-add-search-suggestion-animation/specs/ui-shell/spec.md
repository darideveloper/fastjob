## ADDED Requirements

### Requirement: Vendored Typed.js and search-suggestion module loaded alongside combobox.js
The Typed.js library and the search-suggestion module SHALL be loaded in the `{% block extra_js %}` of each template that contains a `[data-filter-widget]` — currently `templates/home.html` and `templates/dashboard/index.html`. The scripts SHALL be loaded in this order after `combobox.js`: (1) `static/js/vendor/typed.min.js`, (2) `static/js/search-suggestion.js`.

Loading in the child templates (rather than in `base.html`) ensures `combobox.js` executes first, so the `window.FastJobFilter` namespace (including `optionsPromise` and `readyPromise`) is available before `search-suggestion.js` runs. Pages without a filter widget (login, pricing, etc.) will not load these scripts at all, keeping page weight minimal.

No additional third-party CDN `<script>` tags SHALL be introduced by this change. The vendored Typed.js file is the only new dependency, and it is served from the same origin as the FastJob application (consistent with the "Drawer JS does not depend on a third-party framework" and "Scroll-Reveal Animation System" requirements that prohibit external CDN dependencies).

The `search-suggestion.js` module SHALL:
- Await `window.FastJobFilter.readyPromise` (which resolves only after both `optionsPromise` has resolved AND `initWidgets()` has completed, so combobox containers are fully initialised and `optionsData` is available on the namespace)
- Generate 10 random `"{Area} en {Location}..."` strings from `window.FastJobFilter.optionsData`, capitalising the first letter of each value (since the API returns lowercase names)
- Store a parallel `stringMeta` array mapping each display string to its original lowercase `{area, location}` values for use by the click handler
- Shuffle the generated strings using Typed.js's `shuffle: true` option
- Initialise Typed.js on each `[data-search-suggestion]` element with `typeSpeed: 50`, `backSpeed: 30`, `backDelay: 2000`, `loop: true`, `showCursor: true`
- Attach a click handler that resolves the current string via Typed.js internal state (`typed.sequence[typed.arrayPos]` → `typed.strings[...]`) rather than parsing `el.textContent`, because the displayed text can be mid-word during animation; the handler then looks up the original area/location values from the `stringMeta` array and calls `window.FastJobFilter.addValue()` for each match
- Locate the parent `[data-filter-widget]` via `el.parentElement.querySelector('[data-filter-widget]')` instead of `el.closest()`, because on the landing page the suggestion span is a `<div>` sibling of the widget rather than a descendant
- Attach focus/blur listeners on all combobox text inputs within the same `[data-filter-widget]` to pause/resume the Typed.js instance
- Check `window.matchMedia('(prefers-reduced-motion: reduce)')` at init time; if the media query matches, render a single static string and skip Typed.js initialisation entirely
- Fall back to a static hint (`"Busca por sector y ubicación"`) if the options data has insufficient variety (< 2 areas or < 2 locations) or if the options fetch failed

`combobox.js` SHALL be updated to expose a `window.FastJobFilter` namespace containing four things: (1) `optionsPromise` — a getter returning the memoised fetch promise so `search-suggestion.js` can await it without a duplicate API call, (2) `optionsData` — set to `{areas, locations}` after `initWidgets()` completes, (3) `readyPromise` — a promise that resolves only after all combobox widgets on the page have been initialised (i.e. after `initWidgets()` has completed and each container's `_addValue` is available), and (4) `addValue(widgetElement, comboboxType, value)` — a function that finds the `[data-combobox="<comboboxType>"]` container inside the given widget and calls its internal `addValue` method to programmatically add a selected pill. This avoids exposing the entire IIFE internals; only the four hooks that `search-suggestion.js` needs are made public.

Internally, `combobox.js` SHALL store each initialized combobox's `addValue` function (currently a private closure variable inside `initCombobox`) on the container element — either directly as a property (e.g. `container._addValue = addValue`) or via a `WeakMap` — so that the public `addValue()` helper can look it up by DOM element.

#### Scenario: Typed.js is loaded from the FastJob origin, not from a CDN
- **GIVEN** a page containing a `[data-filter-widget]` (e.g. the landing page or dashboard)
- **WHEN** the page is rendered
- **THEN** the HTML includes a `<script src="/static/js/vendor/typed.min.js">` tag
- **AND** no `<script>` tag references a third-party CDN domain for Typed.js
- **AND** the version comment above the tag identifies the Typed.js version and source URL

#### Scenario: search-suggestion.js is loaded only on pages with filter widgets
- **GIVEN** the landing page or dashboard
- **WHEN** the page is rendered
- **THEN** the HTML includes `<script>` tags in `{% block extra_js %}` in the order: `combobox.js`, `typed.min.js`, `search-suggestion.js`
- **GIVEN** a page without a filter widget (e.g. `/accounts/login/` or `/payments/paquetes/`)
- **WHEN** the page is rendered
- **THEN** neither `typed.min.js` nor `search-suggestion.js` is loaded

#### Scenario: No duplicate API calls from the suggestion module
- **GIVEN** the landing page or dashboard loads
- **WHEN** both `combobox.js` and `search-suggestion.js` initialise
- **THEN** only one HTTP request to `/api/companies/filter-options/` is made
- **AND** `search-suggestion.js` awaits the promise already memoised by `combobox.js`

#### Scenario: Suggestion module waits for combobox initialization
- **GIVEN** the landing page or dashboard loads
- **WHEN** `search-suggestion.js` awaits `window.FastJobFilter.readyPromise`
- **THEN** the promise resolves only after all `[data-combobox]` containers have been initialised and their `_addValue` methods are available on the DOM
- **AND** calling `window.FastJobFilter.addValue(widget, 'area', 'abogados')` after `readyPromise` resolves successfully adds a pill to the area combobox

#### Scenario: Suggestion strings capitalise the first letter of each value
- **GIVEN** the filter-options response returns `areas: ["abogados", "tecnologia"]` and `locations: ["madrid", "barcelona"]`
- **WHEN** `search-suggestion.js` generates suggestion strings
- **THEN** each string has the format `"{CapitalisedArea} en {CapitalisedLocation}..."` (e.g. `"Abogados en Madrid..."`, `"Tecnologia en Barcelona..."`)
- **AND** the values passed to `addValue()` for combobox pre-fill remain lowercase (e.g. `"abogados"`, `"madrid"`) to match the whitelist

#### Scenario: Click handler resolves the correct string via Typed.js internal state, not DOM parsing
- **GIVEN** the suggestion animation is mid-type, displaying `"Aparatos e"` (incomplete fragment of `"Aparatos en Madrid..."`)
- **WHEN** the visitor clicks the suggestion element
- **THEN** the handler reads `typed.sequence[typed.arrayPos]` to get the full `"Aparatos en Madrid..."` string
- **AND** matches `"aparatos"` and `"madrid"` against the whitelist via the `stringMeta` lookup
- **AND** both comboboxes are pre-filled correctly

#### Scenario: Script URLs carry a cache-busting query parameter
- **WHEN** any page containing a `[data-filter-widget]` is rendered
- **THEN** each `{% static %}` script tag in `{% block extra_js %}` has a `?v=N` query parameter (e.g. `combobox.js?v=5`)
- **AND** the three script tags use the same version number for consistency