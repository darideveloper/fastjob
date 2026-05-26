# Change: Add animated search-suggestion text to filter sections

## Why
The filter sections on both the landing page and dashboard currently present static labels ("Sector / Area" and "Ubicacion") with type-to-search placeholders. New visitors may not realise the comboboxes support free-text filtering, and authenticated users may not understand the full range of searchable combinations. A typewriter-animated suggestion line under the section heading — cycling through real area+location combos like "Abogados en Madrid..." — makes the search affordance immediately visible and invites interaction.

## What Changes
- Add a `<span data-search-suggestion>` element under the section heading on both the landing page and the dashboard, displaying a typewriter-animated suggestion string built from live filter-option data
- Vendor the Typed.js library (~7 KB minified) into `static/js/vendor/typed.min.js` and load it via `{% block extra_js %}` in `home.html` and `dashboard/index.html` (after `combobox.js`)
- Create `static/js/search-suggestion.js` (94 lines) that waits for the combobox's cached `/api/companies/filter-options/` response (via `window.FastJobFilter.readyPromise`), generates 10 random "{Area} en {Location}..." strings, and initialises Typed.js on the suggestion element
- Store a `stringMeta` lookup alongside display strings so the click handler can resolve the original area/location values via Typed.js internal state (`typed.sequence`, `typed.arrayPos`, `typed.strings`) rather than parsing the DOM text mid-animation — this fixes clicks during typing/backspacing
- Locate the `[data-filter-widget]` parent by first checking if `el.parentElement` itself matches `[data-filter-widget]` (dashboard — the suggestion span is a child) before falling back to `parentElement.querySelector()` (landing page — the suggestion span is a sibling); a plain `querySelector` fails on the dashboard because it only searches descendants, not the element itself
- Add `?v=N` cache-busting query parameters to all three script URLs to work around CDN caching (DigitalOcean Spaces CDN caches for 24 hours)
- Load `typed.min.js` and `search-suggestion.js` in `{% block extra_js %}` of `home.html` and `dashboard/index.html` (after `combobox.js`), not in `base.html`
- Make the animated text interactive: clicking the currently displayed suggestion pre-fills the area and location comboboxes with that combination (triggers the existing `onChange` callback, which updates the company count); on the dashboard this fills the form but does NOT auto-submit
- **Clear all existing pills before adding new ones** when clicking a suggestion — exposed `clearWidget(widgetElement)` in `window.FastJobFilter` which iterates both comboboxes and calls `_removeAll()`, preventing accumulated filter state from creating visual confusion
- Pause the typing animation while any combobox input is focused (reduces distraction while typing)
- Respect `prefers-reduced-motion`: when enabled, show a single static suggestion instead of the animation
- Add `aria-hidden="true"` to the animated element so screen readers present the static section heading, not the transient animation
- Style the suggestion element as `text-brand text-sm cursor-pointer hover:text-brand-dark transition` to signal clickability; **omit `motion-safe:transition-all`** since the `transition-all` class causes CSS to smoothly animate width/height (500ms) each time Typed.js adds/removes a single character (50ms interval), creating a jittery visual conflict

## Impact
- Affected specs: **landing** (new requirement for the suggestion element on the public company-finder section), **dashboard** (new requirement for the suggestion element on the dashboard filters section), **ui-shell** (new first-party JS module added to the global asset list, vendor dependency)
- Affected code: `templates/home.html`, `templates/dashboard/index.html` (script tags in `{% block extra_js %}`), `static/js/search-suggestion.js` (new), `static/js/vendor/typed.min.js` (new vendored dependency), `static/js/combobox.js` (minor: expose `window.FastJobFilter` namespace with `optionsPromise`, `readyPromise`, and `addValue` helper)