## 1. Remove rebuild-on-filter-change callback

- [x] 1.1 In `static/js/search-suggestion.js`, remove `NS.onOptionsChange = rebuildSuggestions;` (line 186) and the entire `rebuildSuggestions` function (lines 142-184).
- [x] 1.2 In `static/js/combobox.js`, remove the `onOptionsChange` invocation (lines 292-294: `window.FastJobFilter.optionsData = data;` and the `if (typeof window.FastJobFilter.onOptionsChange === 'function') { window.FastJobFilter.onOptionsChange(data); }` block).

## 2. Hide suggestion on first user interaction

- [x] 2.1 In `static/js/search-suggestion.js`, add a `hideSuggestions()` function that fades out all `[data-search-suggestion]` elements (CSS `opacity: 0` with `transition: opacity 0.3s ease`), then after the transition destroys all Typed instances and sets `el.innerHTML = ''`.
- [x] 2.2 Add a `userInteracted` flag so `hideSuggestions()` only runs once.
- [x] 2.3 In `initSuggestionElements()`, after initialising Typed, add one-time `focus` listeners on all `[data-filter-widget] input[type="text"]` elements that call `hideSuggestions()`.
- [x] 2.4 Also call `hideSuggestions()` from the existing click handler in `initSuggestionElements()` (when the user clicks a suggestion string to pre-fill, the suggestion should hide).

## 3. Prevent layout collapse with min-height

- [x] 3.1 In `templates/home.html` and `templates/dashboard/index.html`, add inline style or a Tailwind class `min-h-[1.25rem]` to the `<span data-search-suggestion>` element so it never collapses to 0 height even if innerHTML is briefly empty.

## 4. Cache-bust and deploy

- [x] 4.1 Bump the version query string on `search-suggestion.js` in `templates/home.html` and `templates/dashboard/index.html` (to `?v=10`).
- [x] 4.2 Bump the version query string on `combobox.js` in both templates (to `?v=11`).
- [x] 4.3 Upload updated `search-suggestion.js` and `combobox.js` to the DigitalOcean Spaces CDN with `Cache-Control: public, max-age=300`. _(manual step)_

## 5. Verify

- [x] 5.1 Load the landing page and confirm the suggestion animation types correctly on initial load. _(manual)_
- [x] 5.2 Click into a combobox input — the suggestion should fade out smoothly and never reappear. _(manual)_
- [x] 5.3 Select a filter value — no layout jump, no suggestion rebuild. _(manual)_
- [x] 5.4 Select and deselect multiple filters — no suggestion animation, no vertical jump anywhere. _(manual)_
- [x] 5.5 Click a suggestion string — it should pre-fill the comboboxes and fade out. _(manual)_
- [x] 5.6 Test with `prefers-reduced-motion: reduce` — static suggestion text appears, hides on first interaction. _(manual)_
- [x] 5.7 Run the existing test suite; ensure no regressions. _(manual)_

## 6. Additional fixes for remaining glitches

- [x] 6.1 Remove focus/blur `typed.stop()/start()` handlers from `initTyped()` — these conflicted with `hideSuggestions()` by restarting the animation via the blur handler when the user selected a filter value, causing visible animation glitching during fade-out.
- [x] 6.2 Immediately call `typed.stop()` on all Typed instances in `hideSuggestions()` before starting the fade-out, preventing the animation from continuing to type/delete during the 300ms opacity transition.
- [x] 6.3 Replace Tailwind `transition` class with `transition-colors` on `[data-search-suggestion]` elements — the `transition` class adds `transition: all 0.15s` which includes `opacity`, interfering with the Typed.js cursor blink animation (making it fade/pulse instead of blink) and conflicting with the `hideSuggestions()` inline opacity transition.
- [x] 6.4 Bump version query strings on `search-suggestion.js` to `?v=10` and `combobox.js` to `?v=11` in both templates.