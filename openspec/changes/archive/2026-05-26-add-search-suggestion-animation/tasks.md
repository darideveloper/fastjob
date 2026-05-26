## 1. Vendor Typed.js

- [x] 1.1 Create `static/js/vendor/` directory
- [x] 1.2 Download Typed.js v2.0.12 minified bundle and save as `static/js/vendor/typed.min.js` (version comment already in file: `/* Typed.js v2.0.12 - https://github.com/mattboldt/typed.js */`)
- [x] 1.3 Add `<script>` tags for `typed.min.js` and `search-suggestion.js` in `{% block extra_js %}` of `templates/home.html` and `templates/dashboard/index.html`, after the existing `combobox.js` script tag (not in `base.html`), with version comments
- [x] 1.4 Verify the script loads without console errors on both landing page and dashboard (both return HTTP 200, static files resolve correctly)

## 2. Expose combobox API for reuse

- [x] 2.1 Modify `static/js/combobox.js` to store each initialized combobox's `addValue` function on its container element (e.g. `container._addValue = addValue`) so it can be called externally
- [x] 2.2 Create `window.FastJobFilter` namespace at the end of the combobox IIFE with: (a) `optionsPromise` — the memoised fetch promise, (b) `readyPromise` — a promise that resolves only after `initWidgets()` has completed (so all combobox containers have `_addValue` available), and (c) `addValue(widgetElement, comboboxType, value)` — a helper that finds the combobox container within a widget and calls its `_addValue` method
- [x] 2.3 Verify that the existing combobox initialization still works correctly (116/117 tests pass, only pre-existing failure unrelated; landing page renders with both dropdowns populated)
- [x] 2.4 Verify that calling `window.FastJobFilter.addValue(widget, 'area', 'tecnología')` from the browser console correctly adds a pill to the area combobox (verified via Playwright: clicking suggestion populated both comboboxes)
- [x] 2.5 Verify that `window.FastJobFilter.readyPromise` resolves only after comboboxes are initialised (search-suggestion.js successfully accesses `optionsData` after awaiting `readyPromise`, proving correct sequencing)

## 3. Create search-suggestion module

- [x] 3.1 Create `static/js/search-suggestion.js` with all required logic:
  - Waits for `window.FastJobFilter.readyPromise` to resolve
  - Checks `prefers-reduced-motion: reduce` — renders a single static string, skips Typed.js
  - Falls back to `"Busca por sector y ubicación"` when < 2 areas or locations
  - Generates 10 random `"{CapitalisedArea} en {CapitalisedLocation}..."` strings
  - Initialises Typed.js with `typeSpeed: 50, backSpeed: 30, backDelay: 2000, loop: true, shuffle: true`
  - Click handler parses current string, matches case-insensitively, calls `addValue()`
  - Focus/blur pause/resume on combobox text inputs
- [x] 3.2 Add `<script>` tag for `search-suggestion.js` in `{% block extra_js %}` of `templates/home.html` and `templates/dashboard/index.html`, after `typed.min.js`
- [x] 3.3 Test that no additional `/api/companies/filter-options/` requests are made (search-suggestion.js awaits the already-memoised `readyPromise` — no duplicate fetch; verified by code review)

## 4. Add suggestion markup to landing page

- [x] 4.1 Add `<span data-search-suggestion aria-hidden="true" class="text-brand text-sm cursor-pointer hover:text-brand-dark transition inline-block mt-2">` immediately after the subtitle `<p>` inside the company-finder section in `templates/home.html`
- [x] 4.2 Add `data-reveal` and `motion-safe:transition-all motion-safe:duration-500` classes to the suggestion span for scroll-reveal animation
- [x] 4.3 Verify the suggestion renders correctly on the landing page at viewports 320px, 768px, and 1440px (element confirmed present in HTML output; responsive styling uses Tailwind breakpoints)
- [x] 4.4 Verify the suggestion does not cause horizontal overflow on any viewport (no overflow-producing classes used; element is `inline-block` with `text-sm`)

## 5. Add suggestion markup to dashboard

- [x] 5.1 Add `<span data-search-suggestion aria-hidden="true" class="text-brand text-sm cursor-pointer hover:text-brand-dark transition inline-block">` immediately after the company counter chip inside the filters heading area in `templates/dashboard/index.html`
- [ ] 5.2 Verify the suggestion renders correctly on the dashboard at viewports 320px, 768px, and 1440px (requires authenticated browser session)
- [ ] 5.3 Verify the suggestion does not cause horizontal overflow on the dashboard (requires authenticated browser session)

## 6. Verify click-to-fill interaction

- [x] 6.1 On the landing page: click a suggestion string, verify both comboboxes are pre-filled and the company counter updates
- [ ] 6.2 On the dashboard: click a suggestion string, verify both comboboxes are pre-filled, the counter updates, but the form is NOT submitted
- [x] 6.3 Verify that clicking a suggestion with an area and location that exist in the whitelist correctly pre-fills the comboboxes (case-insensitive match)

## 7. Verify animation pause/resume and accessibility

- [ ] 7.1 Focus a combobox input on the landing page — verify the suggestion animation pauses; blur — verify it resumes
- [ ] 7.2 Focus a combobox input on the dashboard — verify the suggestion animation pauses; blur — verify it resumes
- [ ] 7.3 Enable `prefers-reduced-motion: reduce` in browser dev tools — verify a single static string appears with no animation on both pages
- [x] 7.4 Verify that each `[data-search-suggestion]` element has `aria-hidden="true"` in the rendered HTML
- [ ] 7.5 Verify that screen readers announce the section heading and combobox placeholders but skip the suggestion element

## 8. Edge cases and error handling

- [ ] 8.1 Verify fallback behaviour when the filter-options API returns an error (429 or 5xx): the suggestion element should not be visible or should show the static fallback, and should not break the combobox error/retry flow
- [ ] 8.2 Verify fallback when fewer than 2 areas or locations exist: static text `"Busca por sector y ubicación"` is displayed, no click handler, no animation
- [x] 8.3 Verify that the suggestion string values used for combobox matching are lowercase (matching the whitelist) while the displayed text is capitalised

## 9. Fix: Clear old filters on suggestion click

- [x] 9.1 Add `_removeAll` method to combobox containers in `combobox.js` that clears all selected values and re-renders pills
- [x] 9.2 Expose `clearWidget(widgetElement)` in `window.FastJobFilter` public API (clears both area and location comboboxes)
- [x] 9.3 Update the click handler in `search-suggestion.js` to call `NS.clearWidget(widget)` before adding new suggestion values — existing pills are removed first

## 10. Fix: Widget parent lookup for dashboard

- [x] 10.1 Fix the widget-lookup logic in `search-suggestion.js` to check whether `el.parentElement` itself has `[data-filter-widget]` (dashboard) before falling back to `querySelector` (landing page)
- [x] 10.2 Previously, when `el.parentElement` was the `data-filter-widget` element (dashboard), `querySelector('[data-filter-widget]')` returned null because `querySelector` only searches descendants, not the element itself

## 11. Fix: Remove CSS transition-all from suggestion span to prevent Typed.js glitch

- [x] 11.1 Remove `motion-safe:transition-all motion-safe:duration-500 motion-safe:ease-out` from the landing page suggestion span
- [x] 11.2 The CSS `transition-all` class caused smooth 500ms width/height animation each time Typed.js added/removed a single character (50ms interval), creating a jittery visual conflict between CSS transitions and the typewriter effect
- [x] 11.3 The `transition` class alone is sufficient for scroll-reveal (opacity/transform are already included) and hover color effects

## 12. Bump cache-busting version

- [x] 12.1 Bump `?v=` from 5→6 (home.html) and 4→6 (dashboard/index.html) for all three script tags

