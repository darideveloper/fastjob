## Context

The cascading-filter feature (`add-cascading-filter-options`) wired `rebuildSuggestions()` into the available-filter callback so that suggestion strings would reflect narrowed options. In practice, combining a typing animation + periodic rebuild + DOM clearing causes three visible glitches. The suggestion strings are randomly generated and purely decorative — they don't need to reflect the narrowed taxonomy.

## Goals

- Eliminate all three animation glitches (typing chaos, vertical jump on erase, jump on selection)
- Preserve initial-load typing animation, focus-pause, click-prefill, reduced-motion fallback, and `aria-hidden`
- Make the suggestion animation hide gracefully on first user interaction, never to return

## Non-Goals

- Synchronising suggestion strings with the current filter state (this was the cause of the glitches)
- Replacing Typed.js with a different animation approach
- Changing the suggestion element's styling or position

## Decisions

### Decision: Hide on first interaction instead of rebuild on filter change

**Options considered:**

1. **Rebuild suggestions on filter change** (current behaviour) — causes all three glitches.
2. **Rebuild but preserve layout** (keep Typed, just update strings with `typed.strings = [...]`) — Typed.js doesn't support updating strings without a full destroy+reinit, and the animation still restarts mid-cycle.
3. **Hide on first interaction** — the user has already moved past the suggestion prompt. Clean fade-out, no future glitches. Simplest code change.

**Chosen:** Option 3. Once the user focuses an input or selects a filter value, the suggestion fades out and is destroyed. No rebuild is needed.

### Decision: Use CSS `min-height` for layout stability

Adding `min-height: 1.25rem` (matching `text-sm` line-height) to `[data-search-suggestion]` prevents the element from collapsing during the initial Typed.js teardown/rebuild window. This is only needed during page load initialization, not during rebuild cycles (which we're removing entirely).

### Decision: Remove `onOptionsChange` callback entirely

The `NS.onOptionsChange = rebuildSuggestions` and its invocation in `combobox.js` serve no purpose after hiding on interaction. Removing both simplifies the code and prevents future regressions.

## Risks / Trade-offs

- **Risk**: User sees the suggestion for only a brief moment before hiding. **Mitigation**: The suggestion is just a prompt — once the user starts interacting, they no longer need it. This is standard UX practice for placeholder/suggestion text.
- **Risk**: Removing rebuild-on-filter-change shows suggestions "Abogados en Madrid" even if the user just selected "A Coruña". **Mitigation**: Suggestion strings are random combinations, never meant to be contextually accurate for the current filter state. The user has already started interacting, so the suggestion is irrelevant at that point.
- **Risk**: `hideSuggestions()` sets an inline `transition: opacity 0.3s ease` which overrides the Tailwind `transition` class, but the `transition` class also includes `opacity` — this caused the cursor blink animation to fade/pulse instead of blink. **Mitigation**: Replaced `transition` with `transition-colors` on the suggestion element, which preserves hover effects without interfering with `opacity`.
- **Risk**: The `initTyped()` focus/blur handlers call `typed.stop()`/`typed.start()`. When `hideSuggestions()` is triggered by a focus event, the subsequent blur handler restarts the animation during the fade-out. **Mitigation**: Removed the focus/blur stop/start handlers entirely — with permanent hide-on-first-interaction, pausing the animation is unnecessary and actively harmful.

## Decision: Immediately stop Typed instances on hide

Rather than just setting `opacity: 0` and letting the animation continue running for 300ms before destroy, we now call `typed.stop()` immediately at the start of `hideSuggestions()`. This prevents the text from continuing to type/delete while fading out, eliminating the "typing chaos" glitch during the transition.