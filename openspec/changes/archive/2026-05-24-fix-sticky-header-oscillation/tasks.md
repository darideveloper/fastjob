# Tasks: Fix sticky header oscillation glitch

## 1. Implementation

- [x] 1.1 In `templates/base.html`, update the `update()` function (lines 129–131) to use hysteresis: set `data-scrolled="true"` only when `window.scrollY > 24` (not `> 8`), and restore `"false"` only when `window.scrollY < 4`. Guard `setAttribute` so it only fires when the state actually changes.
- [x] 1.2 In `templates/base.html`, replace `motion-safe:transition-all` with `motion-safe:transition-[height]` on the inner row `<div>` (line 51) and the logo `<img>` (line 55), so only `height` animates during state transitions.

## 2. Verification

- [x] 2.1 **Code check:** Verified `templates/base.html` — no `transition-all` remains in the navbar; hysteresis (enter >24, exit <4) and stateful guard (`cur !== prev`) are in place.
- [x] 2.2 **Manual — confirmed working.** User verified on `https://fastjob.localhost/`.
- [x] 2.3 **Manual — confirmed working.** User verified on mobile viewport.
- [x] 2.4 **Manual — confirmed working.** User verified reduced motion.
- [x] 2.5 `openspec validate fix-sticky-header-oscillation --strict` → valid.
