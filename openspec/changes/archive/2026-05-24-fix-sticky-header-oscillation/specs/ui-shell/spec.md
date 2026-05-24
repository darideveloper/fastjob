# ui-shell delta — Fix sticky header oscillation glitch

## MODIFIED Requirements

### Requirement: Sticky global navbar with elevation transition

The global navbar in `templates/base.html` SHALL be rendered as `position: sticky` with `top: 0` and `z-index: 40`, so it remains visible at the top of the viewport on every page that extends `base.html` (landing, packages, dashboard, auth, mailing landings, error pages).

The navbar SHALL render in one of two visual states, driven by a `data-scrolled` attribute on the `<nav>` element:

- **At-rest state** (`data-scrolled="false"`, applied when `window.scrollY < 4`): the navbar renders with its baseline `shadow-sm`, the inner row height is `h-20` (80 px), and the logo height is `h-14` (per the "Logo & favicon wiring" requirement).
- **Scrolled state** (`data-scrolled="true"`, applied when `window.scrollY > 24`): the navbar renders with `shadow-md`, the inner row height is `h-16` (64 px), and the logo height is `h-11` (44 px).
- **Hysteresis dead zone** (when `window.scrollY ≥ 4` and `window.scrollY ≤ 24`): the navbar SHALL remain in whichever state it was already in. This dampens the oscillation caused by the height-change feedback loop — when the navbar state changes, the sticky element's height shifts (16 px), which affects `scrollY`; the 20 px dead zone prevents that shift from immediately triggering a reverse transition.

The transition between the two states MUST be a CSS transition with duration ≤ 200 ms on the affected properties (`box-shadow`, `height`). The transition MUST be wrapped in a `@media (prefers-reduced-motion: no-preference)` block (or equivalent Tailwind variant) so users with `prefers-reduced-motion: reduce` see an instant state swap with no transition. The CSS transition on the inner row SHALL target only `height` — the inner row MUST NOT use `transition-all`, which would animate padding, margin, or other incidental properties and amplify layout jitter. The logo `<img>` SHALL target only `height` and MUST NOT use `transition-all`. Additionally, the logo SHALL carry a `transition-delay` of 150 ms (`motion-safe:delay-150`) so its height transition starts after the row height change is mostly complete — this prevents the at-rest logo height (56 px) from overflowing the row while the row is mid-transition toward its scrolled height (64 px).

The scroll listener SHALL be a small first-party vanilla JS snippet embedded in `templates/base.html` (consistent with the existing "Drawer JS does not depend on a third-party framework" requirement). It MUST:

- be registered with `{ passive: true }`,
- be throttled with `requestAnimationFrame` (read `window.scrollY` once per frame at most),
- use **hysteresis thresholds** for state transitions (enter scrolled at `24 px`, exit at `4 px`),
- **guard `setAttribute` calls** so the DOM attribute is only updated when the state actually changes (comparing current vs. new value), avoiding unnecessary DOM mutations,
- not introduce any third-party CDN dependency,
- not exceed ~30 lines of inline JS.

#### Scenario: Navbar stays visible while scrolling on every public page
- **GIVEN** an anonymous visitor at viewport 1440 × 900 on `/`, `/payments/paquetes/`, or `/accounts/login/`
- **WHEN** the visitor scrolls the page down by 500 px
- **THEN** the navbar is still visible at the top of the viewport
- **AND** `getComputedStyle(navEl).position` is `"sticky"`

#### Scenario: Navbar elevates after the 24 px scroll threshold
- **GIVEN** the home page rendered at any viewport
- **WHEN** `window.scrollY` transitions from `0` to a value greater than `24`
- **THEN** within ≤ 1 animation frame the `<nav>` element has `data-scrolled="true"`
- **AND** within ≤ 200 ms the computed shadow has changed from `shadow-sm` to `shadow-md`
- **AND** the inner row height has transitioned from `80 px` to `64 px`

#### Scenario: Navbar de-elevates when returning below the 4 px threshold
- **GIVEN** the page is scrolled past the hysteresis dead zone and `data-scrolled="true"`
- **WHEN** the user scrolls back so `window.scrollY < 4`
- **THEN** within ≤ 1 animation frame `data-scrolled="false"` is restored
- **AND** the shadow and inner-row height transition back to their at-rest values

#### Scenario: Hysteresis dead zone prevents oscillation
- **GIVEN** the navbar is in its scrolled state (`data-scrolled="true"`)
- **WHEN** `window.scrollY` fluctuates between `4` and `24` (e.g. due to the height-change feedback loop)
- **THEN** the `data-scrolled` attribute SHALL NOT change
- **AND** the navbar's shadow and inner-row height SHALL remain in their scrolled state
- **AND** no rapid toggle of `data-scrolled` occurs

#### Scenario: Reduced-motion users get an instant state swap
- **GIVEN** a user whose OS reports `prefers-reduced-motion: reduce`
- **WHEN** they scroll past the 24 px threshold or back under the 4 px threshold
- **THEN** the `data-scrolled` attribute still toggles correctly
- **AND** the shadow / height / logo-size change is applied with no CSS transition (duration `0 ms`)

#### Scenario: Sticky navbar does not introduce a third-party script
- **WHEN** the rendered HTML of any page that extends `base.html` is inspected
- **THEN** the sticky-navbar behavior is implemented via an inline `<script>` block (or a first-party `static/js/` file)
- **AND** no new `<script src=…>` referencing a third-party origin has been added by this change

#### Scenario: Mobile drawer still opens and closes under the sticky navbar
- **GIVEN** an anonymous or authenticated visitor at viewport 375 × 667 with the page scrolled past the 16 px threshold
- **WHEN** the visitor taps the hamburger toggle button
- **THEN** the drawer opens anchored to the navbar's bottom edge (not detached from the navbar)
- **AND** the drawer closes correctly on outside click and on Escape, preserving every existing scenario under the "Mobile-collapsing global navbar" requirement
