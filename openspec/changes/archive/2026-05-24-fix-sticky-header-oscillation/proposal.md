# Change: Fix sticky header oscillation glitch near the scroll threshold

## Why

When scrolling past the 8 px threshold on any page that extends `base.html`, the navbar rapidly toggles between its at-rest and scrolled states, causing a visible flickering glitch. The root cause is a **height-change feedback loop**:

1. User scrolls past `scrollY > 8` → `data-scrolled` becomes `"true"`
2. The inner row shrinks from `h-20` (80 px) to `h-16` (64 px) via a 200 ms CSS transition
3. Total page height decreases by 16 px; the browser adjusts the scroll position → `scrollY` drops
4. `scrollY ≤ 8` → `data-scrolled` flips back to `"false"` → the row expands back to 80 px
5. Content shifts down → `scrollY` increases past 8 again
6. Cycle repeats — the navbar oscillates until the user scrolls far enough past the threshold that the height change can no longer push `scrollY` below 8 px

The problem is exacerbated by:
- **Single hard boundary** at `scrollY = 8` with no dead zone (hysteresis), so any fluctuation near that value triggers a state flip
- **`transition-all`** on the inner row (line 51) animates every property, amplifying the layout jitter during transitions

## What Changes

- **Add hysteresis to the scroll listener:** The navbar SHALL enter the scrolled state when `scrollY > 24` and return to the at-rest state when `scrollY < 4`, creating a 20 px dead zone that safely exceeds the 16 px height-change fluctuation and dampens the oscillation.
- **Optimize `setAttribute` calls:** The scroll listener SHALL only call `setAttribute` when the state actually changes (comparing current vs. new value), avoiding unnecessary DOM mutations.
- **Tighten CSS transitions:** Change `motion-safe:transition-all` to `motion-safe:transition-[height]` on the inner row `<div>` (line 51) and the logo `<img>` (line 55), so only relevant properties animate — no padding, margin, or other incidental properties.
- **Stagger the logo animation:** Add `motion-safe:delay-150` on the logo `<img>` so the logo shrink starts 150 ms after the row height change. This prevents the logo (56 px) from overflowing the row mid-transition when the row is near its scrolled height (64 px) but the logo is still at its at-rest size.

## Impact

- **Affected specs:**
  - `ui-shell` — the "Sticky global navbar with elevation transition" requirement is modified to specify hysteresis thresholds and a stateful (not just throttled) scroll listener.
- **Affected code:**
  - `templates/base.html` — scroll listener JS (lines 129–131) and inner-row CSS transition class (line 51).
- **No new third-party dependencies.** The scroll listener remains inline vanilla JS with `requestAnimationFrame` throttling, consistent with the existing first-party-only posture.
- **No Django admin, database, or migration changes.**
- **Accessibility:** No regressions. The `motion-safe:` variant already respects `prefers-reduced-motion`.
