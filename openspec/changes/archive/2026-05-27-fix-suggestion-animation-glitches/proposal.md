# Change: Fix search-suggestion animation glitches in cascading filter context

## Why

When the user selects or changes a filter value, `combobox.js` calls `scheduleAvailableFilters()`, which overwrites `window.FastJobFilter.optionsData` and calls `onOptionsChange()`. That callback is `rebuildSuggestions()` in `search-suggestion.js`, which destroys the active Typed.js instance, clears `innerHTML`, and re-initialises with new random strings. This causes three visible glitches:

1. **Typing chaos**: Each rebuild starts a brand-new animation from scratch while the old one was mid-cycle, producing a jarring effect of one phrase being deleted and another starting mid-interaction.
2. **Vertical jump on erase**: `rebuildSuggestions` sets `el.innerHTML = ''` (line 177), collapsing the `<span>` height from 20px to 0 before Typed.js begins retyping character-by-character. The layout shifts up then back down.
3. **Jump on filter selection**: Selecting a filter value triggers `scheduleAvailableFilters` → `onOptionsChange` → `rebuildSuggestions`, causing the same destroy-and-recreate cycle and layout jump as Bug 2, even though the suggestion text has no meaningful relationship to the new filter state.

## What Changes

- Stop calling `rebuildSuggestions()` from the cascading-filter callback. The suggestion animation is purely decorative and initialized once from the full taxonomy. Rebuilding it on every filter change adds no user value and causes the glitches.
- Instead, hide the suggestion animation on first user interaction (focus or selection on any combobox input) and fade it out smoothly. Once hidden, it never reappears — the user has already engaged with the form.
- Add `min-height` to the `[data-search-suggestion]` element so even if `innerHTML` is briefly empty during the one-time initialisation, the layout never collapses.
- Remove `NS.onOptionsChange = rebuildSuggestions;` from `search-suggestion.js` and the corresponding call in `combobox.js`, since neither serves a purpose after this change.
- Remove the focus/blur `typed.stop()`/`typed.start()` handlers from `initTyped()` in `search-suggestion.js` — they conflicted with `hideSuggestions()` by restarting the animation via the blur handler when the user selected a filter value mid-fade-out, causing visible glitching.
- Immediately call `typed.stop()` on all Typed instances in `hideSuggestions()` before the opacity transition, preventing the animation from continuing to type/delete during the 300ms fade-out.
- Replace the Tailwind `transition` class with `transition-colors` on `[data-search-suggestion]` elements — the `transition` class adds `transition: all 0.15s` including `opacity`, which interfered with the Typed.js cursor blink animation (making it fade/pulse instead of blink) and conflicted with the `hideSuggestions()` inline opacity transition.
- Keep the initial `buildSuggestions`/`initTyped` wiring: suggestions are still built from `filter-options` data on first load, still clickable to pre-fill.

## Impact

- Affected specs: `landing` (Search-suggestion animation requirement), `dashboard` (Search-suggestion animation in dashboard filters requirement)
- Affected code: `static/js/search-suggestion.js`, `static/js/combobox.js`, `templates/home.html`, `templates/dashboard/index.html`
- The suggestion animation still works exactly as spec'd for initial load, click-prefill, reduced-motion, and fallback. The **focus-pause** behaviour is removed since the suggestion now hides permanently on first focus instead. All three glitches (typing chaos, vertical jump on erase, jump on filter selection) are eliminated.