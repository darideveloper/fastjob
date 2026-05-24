# Design: Polish landing interactions, sticky header, larger logo, filter UX

## Context
All five items in this proposal target the chrome and the public landing surface. The work spans two existing capabilities (`ui-shell` and `landing`) and needs to keep the project's first-party-only JS posture and the existing WCAG AA contrast invariants intact.

## Architectural decisions

### 1. Sticky header — CSS `position: sticky`, not JS-driven offset
**Decision:** Use `position: sticky; top: 0; z-index: 40` on the `<nav>` element in `base.html`. The "elevated" state (shadow + reduced padding + compact logo) is toggled by adding `data-scrolled="true"` to the `<nav>` element from a small scroll listener. CSS transitions handle the visual change.

**Rejected alternatives:**
- `position: fixed` + manual top-padding on `<body>`: forces every page that extends `base.html` to know the header height, breaks the existing `min-h-screen flex flex-col` body layout, and complicates the mobile drawer behavior already defined in `ui-shell`.
- IntersectionObserver-based sentinel above the navbar: more elegant than a scroll listener but adds a moving DOM node and a separate sentinel element. The scroll listener is ~10 lines, throttled with `requestAnimationFrame`, fires once per frame at most, and reads only `window.scrollY`.

**Threshold:** 8 px of scroll triggers the transition. Anything smaller than that is jitter from rubber-band scroll; anything larger feels "late" — the elevation should announce that we've left the page-top.

**Transition duration:** 180 ms. Long enough to read as smooth, short enough to never feel laggy. Matches the existing Tailwind `transition` (`150ms`) default with a small bump for the multi-property change.

### 2. Logo size — two-state, not single
**Decision:** At-rest = `h-14` (56 px). Sticky-compact = `h-11` (44 px). Both states use `w-auto` so the 1226:450 aspect ratio is intrinsic. Transition `height` and `width` via the parent's CSS `transition: all 180ms ease-out`.

**Why not a single larger size:** the existing `ui-shell` spec already invokes the no-CLS guarantee via reserved aspect ratio. A static `h-14` would shrink the available vertical space for content on long pages — undesirable for the dashboard. Two states give the brand-first impression at the top and a tight chrome during scroll.

**Verification of "≈ 30 %":** `h-11` → `h-14` is 44 → 56 px = +27.3 %. Tailwind's nearest step above (`h-16` = 64 px) is +45 %, too aggressive. `h-14` is the right "feels like 30 %" anchor.

### 3. Hover and Brand effects — token-based + brand accents
**Decision:** Use existing brand tokens with the Tailwind `hover:` modifier, supplemented by hex-specific brand colors where tokens are absent.

- Primary buttons (already `bg-brand`): `hover:bg-brand-dark` (already in use sporadically) becomes mandatory + add `hover:shadow-md hover:-translate-y-0.5 transition`.
- Secondary/ghost links: `text-gray-700` → `hover:text-brand` (already in use) + add `hover:underline underline-offset-4`.
- Hero CTAs (Landing):
  - "Empezar con Google": white card, `hover:bg-brand-cloud`, `hover:ring-[#4285F4]/50`.
  - "Empezar con Microsoft": dark card (`bg-gray-900`), `hover:ring-[#00A4EF]/50`.
  - Both share: `hover:scale-[1.03] hover:-translate-y-1 hover:shadow-2xl`.
- Login Buttons (`login.html`):
  - "Continuar con Google": `hover:bg-brand-cloud hover:border-[#4285F4]`.
  - "Continuar con Microsoft": `hover:bg-gray-50 hover:border-[#00a4ef]`.
  - Both share: `hover:-translate-y-0.5 hover:shadow-md transition`.

### 4. Filter placeholders — instructional, not labels
**Decision:** Placeholder text follows the pattern `Escribe o elige un <noun> (ej. <example>)…`. The verbs "Escribe" and "elige" make it explicit that the field is a hybrid search-and-pick widget. The parenthetical example anchors the user with a concrete value from the existing whitelist.

**Rejected:** a separate `<label>` above the input ("Sector"). The existing `landing` spec already renders the section under a clear heading ("¿Qué empresas tenemos?"), and an extra label crowds the 320 px viewport — the existing `landing` spec already calls out single-line constraints at that width.

### 5. Dropdown capacity — class swap, not config option
**Decision:** Hard-code `max-h-96` (24 rem = 384 px) on the dropdown `<ul>` in `combobox.js`. The existing row height is `py-2 text-sm` ≈ 36 px per row, so 384 px / 36 ≈ 10.6 visible rows — comfortably ≥ 8 *selectable* options even when the "— Limpiar todos —" helper row consumes one slot at the top of the list (which `combobox.js` renders whenever `selected.length > 0`). The list still scrolls past that capacity via the existing `overflow-y-auto`.

**Why not `max-h-80` (320 px ≈ 8.8 rows):** while 8.8 rows nominally satisfies "show 8 options", the dropdown prepends a "— Limpiar todos —" helper row when any pill is selected. Under `max-h-80`, visitors mid-flow would see 7 selectable options + 1 clear-all = 8 visible rows, technically meeting the literal count but falling short of 8 *selectable* options. `max-h-96` removes that ambiguity.

**Rejected:** exposing a `data-max-visible` attribute on the container. YAGNI — only the landing widget consumes this code today, and the dashboard widget (same component) benefits from the same change uniformly.

## Open questions
- Should the sticky behavior also apply on the dashboard? The proposal says yes (it's part of `base.html`, which the dashboard extends). The dashboard never had a sticky header before; if the team prefers to keep dashboard chrome stationary, we can scope the JS to only attach the listener when `<body>` has a `data-public-page` attribute and add that attribute only on landing/packages/auth templates. Flagged for the apply stage.

## Risk register
- **CLS during sticky transition:** mitigated by keeping `<nav>` height changes via `height` (not `min-height`) and by reserving logo aspect-ratio (already required by `ui-shell`).
- **Mobile drawer interaction:** the existing `ui-shell` spec defines drawer open/close behavior. Sticky navbar must keep the drawer anchored to the navbar bottom edge, not the viewport top, so scrolling the drawer-open page does not detach the drawer. Verified by reusing the existing drawer markup (drawer is a sibling of the navbar's inner row, so it inherits sticky positioning naturally).
- **Reduced-motion:** the `transition: all 180ms` MUST be wrapped in a `@media (prefers-reduced-motion: no-preference)` block so users with the reduce-motion preference see instant state swaps.
