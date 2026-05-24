# Design: Scroll-Reveal & Hover Animation System

## Context

FastJob uses Django Templates + Tailwind CSS (CDN) with no build step and minimal custom JS (navbar toggle, combobox widget). The project has a strict "no new third-party dependencies" posture (see `ui-shell` spec: "Drawer JS does not depend on a third-party framework"). Any animation system must be zero-dependency, lightweight, and accessible.

The site currently has one scroll-aware behavior (navbar shadow on scroll) and basic Tailwind `transition` classes on buttons/links. There is no CSS file — all styles are inline Tailwind classes.

## Goals / Non-Goals

### Goals
- Elements slide-fade into view as the user scrolls, giving the landing page and other pages a modern, dynamic feel
- Cards and icons respond to hover with subtle lift/shadow/transform, conveying interactivity and polish
- Full accessibility: users who prefer reduced motion see no animation (elements render in their final state)
- Zero new external dependencies — pure CSS + ~30 lines of IntersectionObserver
- Staggered entrance for sibling grid items (feature cards, pricing cards, stats) so builds feel choreographed
- Consistent hover vocabulary across all client-facing templates

### Non-Goals
- Page-load skeleton screens or LCP optimization
- Parallax effects or scroll-jacking
- Complex keyframe animations (e.g., Lottie, SVG morph)
- Animation on the dashboard activity table rows (functional, not marketing)
- Counting-up number animations on the success page (can be added later but not in this change)

## Decisions

### 1. IntersectionObserver + attribute-removal pattern (chosen)

**How it works:**
- Elements that should animate in get `data-reveal` (plus optional `data-reveal-delay="N"` for stagger)
- CSS rule `[data-reveal] { opacity: 0 !important; transform: translateY(1.5rem) !important }` hides them initially — `!important` guarantees the hidden state wins over any Tailwind utility regardless of CSS source order or specificity
- When the observer sees an element enter the viewport (threshold 0.15), it looks for a nearest ancestor with `data-reveal-stagger="M"`, computes the final delay as `parseInt(delay) × parseInt(stagger)`, applies the computed `transition-delay` via inline style, then removes `data-reveal` and `data-reveal-delay`
- The element then transitions from hidden → visible via Tailwind `motion-safe:transition-all motion-safe:duration-700 motion-safe:ease-out` classes that were already present but blocked by the `data-reveal` rule
- `@media (prefers-reduced-motion: reduce)` overrides `[data-reveal]` to `opacity: 1 !important; transform: none !important; transition: none !important` so elements are always visible for users who need it

**Alternatives considered:**
- **AOS (Animate on Scroll)** — 14 KB JS library, adds `data-aos` attributes, duplicate transitions, conflicts with Tailwind transitions. Rejected: unnecessary dependency and weight.
- **CSS-only `@keyframes` with `animation-timeline: view()`** — Not yet supported in Firefox (only Chromium). Rejected: insufficient browser support.
- **GSAP ScrollTrigger** — Heavy (28 KB+), commercial license complexity. Rejected: overkill for simple fade-slide.

### 2. Stagger via `data-reveal-delay` + `data-reveal-stagger` attributes

Instead of hardcoding millisecond delay values in templates, elements inside dynamic `{% for %}` loops use `data-reveal-delay="{{ forloop.counter0 }}"` with a multiplier defined on a parent wrapper via `data-reveal-stagger="150"` (or `"100"` for 100ms intervals). The observer script computes the final delay as `parseInt(delay) × parseInt(stagger)` and applies it as `transition-delay`. For static elements not in loops (landing page features, trust cards), the delay value is used directly in milliseconds.

This approach avoids Django template math (no `forloop.counter0 * 150` needed), keeps templates readable, and allows a single stagger wrapper to control the timing for an entire grid.

### 3. Hover effects via Tailwind utility classes

No custom CSS for hovers — all hover animations use existing or added Tailwind classes on the elements themselves. This keeps the animation vocabulary discoverable and consistent:
- Cards: `hover:shadow-md hover:-translate-y-0.5 motion-safe:transition-all motion-safe:duration-200`
- Icon containers: `motion-safe:transition-transform motion-safe:duration-200 hover:scale-110`
- Pricing cards: `hover:shadow-lg hover:-translate-y-1 motion-safe:transition-all motion-safe:duration-200`
- Success checkmark: `@keyframes scale-in` bounce (only non-reveal animation that needs a custom keyframe)

### 4. Custom CSS file (`static/css/reveal.css`)

Single new CSS file loaded via `<link>` in `base.html` **before** the Tailwind CDN `<script>` tag. Contains:
- `[data-reveal]` initial hidden state (`opacity: 0 !important; transform: translateY(1.5rem) !important`) — `!important` prevents Tailwind utilities from overriding the hidden state regardless of CSS load order
- `[data-reveal="slide-down"]` variant (`transform: translateY(-1.5rem) !important`)
- `@media (prefers-reduced-motion: reduce)` override: `opacity: 1 !important; transform: none !important; transition: none !important` for all `[data-reveal]` and variant selectors — `transition: none !important` prevents any inherited transition from producing a visual shift under reduced-motion
- `@keyframes scale-in` for the success checkmark

### 5. Reveal script location

Inline `<script>` in `base.html` just before `</body>`, following the same pattern as the existing navbar scroll script. No separate JS file needed — the observer is ~30 lines.

## Reveal Target Inventory

### Landing (`home.html`)
| Element | Delay | Effect |
|---------|-------|--------|
| Hero h1 | 0 | fade-up |
| Hero subtitle | 100ms | fade-up |
| Hero CTA row | 200ms | fade-up |
| "Cómo funciona" h2 | 0 | fade-up |
| Feature card 1 | 0 | fade-up |
| Feature card 2 | 100ms | fade-up |
| Feature card 3 | 200ms | fade-up |
| Feature card 4 | 300ms | fade-up |
| "Diseñado para máxima entregabilidad" h2 | 0 | fade-up |
| Trust card 1 | 0 | fade-up |
| Trust card 2 | 100ms | fade-up |
| Trust card 3 | 200ms | fade-up |
| Finder section h2 | 0 | fade-up |
| Finder subtitle p | 100ms | fade-up |
| Finder card | 200ms | fade-up |
| Finder CTA | 300ms | fade-up |

### Pricing (`packages.html`)
| Element | Delay | Effect |
|---------|-------|--------|
| Header (h1 + p) | 0 | fade-up |
| Pricing card 1 | 0 | fade-up |
| Pricing card 2 | 150ms | fade-up |
| Pricing card 3 | 300ms | fade-up |
| Stripe trust line | 0 | fade |
| Social proof line | 100ms | fade-up |

### Dashboard (`dashboard/index.html`)
| Element | Delay | Effect |
|---------|-------|--------|
| Pause banner (if present) | 0 | slide-down |
| Dashboard header | 0 | fade-up |
| Stat card 1 | 0 | fade-up |
| Stat card 2 | 100ms | fade-up |
| Stat card 3 | 200ms | fade-up |
| Stat card 4 | 300ms | fade-up |
| CV list card | 0 | fade-up |
| Filters card | 100ms | fade-up |
| Danger zone card | 200ms | fade-up |
| Activity card | 0 | fade-up |

### Login (`account/login.html`)
| Element | Delay | Effect |
|---------|-------|--------|
| Login card | 0 | fade-up |

### Success (`payments/success.html`)
| Element | Delay | Effect |
|---------|-------|--------|
| Checkmark icon | 0 | scale-in (keyframe) |
| h1 | 150ms | fade-up |
| Credits number | 300ms | fade-up |
| CTA button | 450ms | fade-up |

### Error pages (404, 500)
| Element | Delay | Effect |
|---------|-------|--------|
| Card | 0 | fade-up |

### Delete account (`dashboard/delete_account.html`)
| Element | Delay | Effect |
|---------|-------|--------|
| Card container | 0 | fade-up |

## Hover Target Inventory

### Landing
| Element | Current | Added |
|---------|---------|-------|
| Feature card div | none | `hover:shadow-md hover:-translate-y-1 motion-safe:transition-all motion-safe:duration-200` |
| Feature icon wrapper (rounded-2xl) | none | `motion-safe:transition-transform motion-safe:duration-200 group-hover:scale-110` (card becomes `group`) |
| Trust card div | none | `hover:shadow-md hover:-translate-y-0.5 motion-safe:transition-all motion-safe:duration-200` |
| Trust "✓" icon | none | `motion-safe:transition-transform motion-safe:duration-200 group-hover:scale-125` (card becomes `group`) |
| Finder CTA arrow icon | none | `motion-safe:transition-transform motion-safe:duration-200 group-hover:translate-x-1` (link becomes `group`) |

### Pricing
| Element | Current | Added |
|---------|---------|-------|
| Package card div | only shadow-sm/ring on recommended | `hover:shadow-lg hover:-translate-y-1 motion-safe:transition-all motion-safe:duration-200` |
| Checkmark SVG in `<li>` | none | `motion-safe:transition-transform motion-safe:duration-150 group-hover:scale-110` (`<li>` becomes `group`) |

### Dashboard
| Element | Current | Added |
|---------|---------|-------|
| Stat card div | none | `hover:shadow-md hover:border-brand/20 motion-safe:transition-all motion-safe:duration-200` |

## Risks / Trade-offs

- **CSS specificity**: The `[data-reveal]` hidden state uses `!important` declarations to guarantee it wins over Tailwind utility classes regardless of CSS source order. Without `!important`, Tailwind's generated utilities (which are injected at runtime by the CDN) could override the `[data-reveal]` rule if the specificity is equal and Tailwind's styles are processed later. The `!important` is semantically appropriate here — it's a deliberate "suppress this element until observed" override.
- **FOIC (Flash of Invisible Content)**: Hero elements (h1, subtitle, CTA) are above the fold and will be invisible (`opacity: 0`) until the observer script runs. On fast connections this is imperceptible (~16ms). On slow connections, there's a risk that the observer script delays because of JS execution ordering. Mitigation: the observer script is inline at the end of `<body>`, executes synchronously, and runs `DOMContentLoaded`-independent observation. The `<link>` for `reveal.css` loads before the Tailwind script, ensuring the hidden state is applied before first paint.
- **SEO**: Google renders JavaScript and observes attributes being removed, so content is still indexed. The IntersectionObserver is a standard web API.
- **Performance**: 30 lines of JS + CSS transitions have near-zero runtime cost. The observer unobserves elements after revealing them, so ongoing scroll handling is minimal.
- **Accessibility**: Fully compliant — `prefers-reduced-motion: reduce` disables all animations and suppresses transitions (`transition: none !important`). No `tabindex` or ARIA changes needed (reveal is decorative, not semantic).
- **Template conflicts**: The active `refresh-landing-shell-and-cv-attachment-copy` change modifies `home.html`, `packages.html`, `base.html`, and `dashboard/index.html`. Adding `data-reveal` attributes to these templates should be applied **after** that change lands to avoid merge conflicts. The `add-auto-upload-cv-on-select` change modifies the CV upload form in `dashboard/index.html`; `data-reveal` attributes on the surrounding cards are additive and should not conflict.

## Migration Plan

1. Add `static/css/reveal.css` (with `!important` declarations) and the observer script in `base.html`
2. Add `<link>` for `reveal.css` **before** the Tailwind CDN `<script>` tag in `base.html`
3. Mark up templates with `data-reveal`, `data-reveal-delay`, and `data-reveal-stagger` attributes
4. Add hover transition classes to card and icon elements
5. Visual QA on all affected pages at 320px, 768px, and 1440px
6. Verify `prefers-reduced-motion` override works (elements visible immediately, no transforms, no transitions)
7. Verify CSS specificity: confirm `[data-reveal]` hidden state wins over Tailwind utilities even when the `<link>` is after the `<script>` tag
8. **Apply after** the `refresh-landing-shell-and-cv-attachment-copy` change to avoid merge conflicts on shared templates (`home.html`, `packages.html`, `base.html`, `dashboard/index.html`)
9. No rollback needed — the change is purely additive (CSS+attribute), removing `data-reveal` attributes reverts to static rendering

## Open Questions

None — the approach is fully specified.