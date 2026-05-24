# ui-shell delta — Polish landing interactions, sticky header, larger logo

## ADDED Requirements

### Requirement: Sticky global navbar with elevation transition
The global navbar in `templates/base.html` SHALL be rendered as `position: sticky` with `top: 0` and `z-index: 40`, so it remains visible at the top of the viewport on every page that extends `base.html` (landing, packages, dashboard, auth, mailing landings, error pages).

The navbar SHALL render in one of two visual states, driven by a `data-scrolled` attribute on the `<nav>` element:

- **At-rest state** (`data-scrolled="false"`, applied when `window.scrollY ≤ 8`): the navbar renders with its baseline `shadow-sm`, the inner row height is `h-20` (80 px), and the logo height is `h-14` (per the modified "Logo & favicon wiring" requirement).
- **Scrolled state** (`data-scrolled="true"`, applied when `window.scrollY > 8`): the navbar renders with `shadow-md`, the inner row height is `h-16` (64 px), and the logo height is `h-11` (44 px).

The transition between the two states MUST be a CSS transition with duration ≤ 200 ms on the affected properties (`box-shadow`, `height`, transformed-by-height of the logo). The transition MUST be wrapped in a `@media (prefers-reduced-motion: no-preference)` block (or equivalent Tailwind variant) so users with `prefers-reduced-motion: reduce` see an instant state swap with no transition.

The scroll listener SHALL be a small first-party vanilla JS snippet embedded in `templates/base.html` (consistent with the existing "Drawer JS does not depend on a third-party framework" requirement). It MUST:

- be registered with `{ passive: true }`,
- be throttled with `requestAnimationFrame` (read `window.scrollY` once per frame at most),
- not introduce any third-party CDN dependency,
- not exceed ~25 lines of inline JS.

#### Scenario: Navbar stays visible while scrolling on every public page
- **GIVEN** an anonymous visitor at viewport 1440 × 900 on `/`, `/payments/paquetes/`, or `/accounts/login/`
- **WHEN** the visitor scrolls the page down by 500 px
- **THEN** the navbar is still visible at the top of the viewport
- **AND** `getComputedStyle(navEl).position` is `"sticky"`

#### Scenario: Navbar elevates after the 8 px scroll threshold
- **GIVEN** the home page rendered at any viewport
- **WHEN** `window.scrollY` transitions from `0` to a value greater than `8`
- **THEN** within ≤ 1 animation frame the `<nav>` element has `data-scrolled="true"`
- **AND** within ≤ 200 ms the computed shadow has changed from `shadow-sm` to `shadow-md`
- **AND** the inner row height has transitioned from `80 px` to `64 px`

#### Scenario: Navbar de-elevates when returning to the top
- **GIVEN** the page is scrolled past the threshold and `data-scrolled="true"`
- **WHEN** the user scrolls back so `window.scrollY ≤ 8`
- **THEN** within ≤ 1 animation frame `data-scrolled="false"` is restored
- **AND** the shadow and inner-row height transition back to their at-rest values

#### Scenario: Reduced-motion users get an instant state swap
- **GIVEN** a user whose OS reports `prefers-reduced-motion: reduce`
- **WHEN** they scroll past or back over the 8 px threshold
- **THEN** the `data-scrolled` attribute still toggles correctly
- **AND** the shadow / height / logo-size change is applied with no CSS transition (duration `0 ms`)

#### Scenario: Sticky navbar does not introduce a third-party script
- **WHEN** the rendered HTML of any page that extends `base.html` is inspected
- **THEN** the sticky-navbar behavior is implemented via an inline `<script>` block (or a first-party `static/js/` file)
- **AND** no new `<script src=…>` referencing a third-party origin has been added by this change

#### Scenario: Mobile drawer still opens and closes under the sticky navbar
- **GIVEN** an anonymous or authenticated visitor at viewport 375 × 667 with the page scrolled past the 8 px threshold
- **WHEN** the visitor taps the hamburger toggle button
- **THEN** the drawer opens anchored to the navbar's bottom edge (not detached from the navbar)
- **AND** the drawer closes correctly on outside click and on Escape, preserving every existing scenario under the "Mobile-collapsing global navbar" requirement

### Requirement: Brand-matched hover affordance on every interactive control
Every `<a>`, `<button>`, and link-styled element rendered on a final-user screen (landing, packages, dashboard chrome, auth, mailing landings, error pages) MUST present a brand-matched hover state. The hover state MUST be implemented using existing `brand.*` tokens — no hardcoded hex colors, no new utility classes — and MUST be paired with a `transition` so the state change is smooth (≤ 200 ms).

The hover treatment MUST follow these per-variant rules:

- **Primary-fill buttons** (currently `bg-brand text-white`): on hover MUST gain `bg-brand-dark` background and SHOULD gain a visible elevation cue (`hover:shadow-md` and/or `hover:-translate-y-0.5`). The `transition` utility MUST be present so the change animates instead of snapping.
- **White-fill buttons on dark backdrops** (e.g. "Empezar con Google"): on hover MUST gain `bg-brand-cloud` (`#E6F2FF`) background and SHOULD gain a brand-matched focus ring (e.g., `#4285F4/50`).
- **Dark-fill buttons on dark backdrops** (e.g. "Empezar con Microsoft"): on hover SHOULD gain a brand-matched focus ring (e.g., `#00A4EF/50`).
- **Ghost links / nav links** (currently `text-gray-700` or `text-brand-ink`): on hover MUST gain `text-brand` color.

The hover state MUST NOT be the sole visual signal for an interactive element — the existing focus-ring requirement ("Visible focus ring on every interactive element") continues to apply for keyboard users and is unaffected by this requirement.

#### Scenario: Primary-fill CTA shows brand-matched hover
- **GIVEN** any primary-fill CTA on any final-user screen (e.g. "Empezar gratis" in the anonymous navbar, "Ver paquetes y empezar" on the home page, the per-package buy buttons on `/payments/paquetes/`)
- **WHEN** the user hovers the element with a pointer device
- **THEN** the computed `background-color` becomes `brand.dark` (`#003D99`)
- **AND** a `transition` lasting ≤ 200 ms animates the change
- **AND** a `box-shadow` of at least `shadow-md` intensity is applied

#### Scenario: Hero white-fill CTA hover preserves AA contrast
- **GIVEN** the "Empezar con Google" hero CTA on the home page
- **WHEN** the user hovers it
- **THEN** the background becomes `brand.cloud` (`#E6F2FF`)
- **AND** the text color remains `brand.dark` (`#003D99`)
- **AND** the resulting contrast ratio remains ≥ 4.5 : 1

#### Scenario: Social login buttons use brand-specific accents
- **GIVEN** the login page or hero CTAs
- **WHEN** the user hovers a Google-branded button
- **THEN** it MAY use the brand-specific blue hex `#4285F4` for borders or focus rings
- **WHEN** the user hovers a Microsoft-branded button
- **THEN** it MAY use the brand-specific blue hex `#00A4EF` (or `#00a4ef`) for borders or focus rings

#### Scenario: Ghost navbar links gain brand-blue color on hover
- **GIVEN** the anonymous navbar at viewport ≥ md (768 px)
- **WHEN** the user hovers any of "Paquetes" or "Iniciar sesión"
- **THEN** the computed text color transitions to `brand.DEFAULT` (`#007BFF`) within ≤ 200 ms

#### Scenario: No legacy or hardcoded color appears in hover classes (except brand-specific social colors)
- **WHEN** `rg -n "hover:" templates/ static/` is run after this change
- **THEN** every match references either a `brand.*` token, a permitted neutral gray, or a semantic status color
- **AND** specific exceptions are allowed for brand-official hexes in social login buttons (`#4285F4`, `#00A4EF`)
- **AND** no `hover:bg-indigo-*` or `hover:text-indigo-*` survives in any template

## MODIFIED Requirements

### Requirement: Logo & favicon wiring
`templates/base.html` SHALL render the FastJob brand mark using the assets at `static/images/fastjob-logo.{webp,png}` (not an inline SVG placeholder) and SHALL declare favicon links pointing to `static/images/favicon.{ico,png}`.

The logo MUST be rendered inside a `<picture>` element with a WebP `<source>` and a PNG `<img>` fallback. Because the source asset is **1226 × 450** (aspect ratio ≈ 2.72 : 1), the markup MUST NOT specify mismatched `width`/`height` attributes that would distort the wordmark. Instead, the `<img>` MUST anchor only its rendered height via Tailwind height-only classes (height anchored, `w-auto` everywhere) and let the width follow the intrinsic ratio. The wrapper element MUST carry `style="aspect-ratio: 1226 / 450"` (or an equivalent reserved-size mechanism) so no CLS occurs while the asset loads. The `<img>` MUST have `alt="FastJob"`.

The navbar logo MUST present **two rendered sizes**, driven by the same `data-scrolled` attribute on the `<nav>` element introduced by the "Sticky global navbar with elevation transition" requirement:

- **At-rest size** (`data-scrolled="false"`): the navbar logo `<img>` MUST render at `h-14` (56 px) tall — a ≈ 27 % increase over the previous `h-11` (44 px) baseline, satisfying the brand-first impression at the page top.
- **Sticky-compact size** (`data-scrolled="true"`): the navbar logo MUST render at `h-11` (44 px) tall, matching the previous baseline and keeping vertical chrome compact while the user scrolls.

The transition between the two sizes MUST use the same CSS transition (duration ≤ 200 ms, respecting `prefers-reduced-motion`) defined for the sticky-navbar elevation transition. The aspect-ratio reservation on the wrapper MUST keep CLS at zero throughout the transition.

The logo on `account/login.html`, `account/logout.html`, the socialaccount templates, and the unauthenticated email-landing cards (`mailing/cv_not_found.html`, `mailing/cv_revoked.html`, `mailing/unsubscribe.html`, `mailing/unsubscribe_confirm.html`) MUST continue to use the same asset at `h-14` (their existing card-level size, as currently rendered in `templates/account/login.html`). These contexts are static cards, not sticky chrome, so they are not affected by the navbar's two-state behavior.

#### Scenario: Navbar logo at-rest uses the larger size
- **GIVEN** any page that extends `base.html`, freshly loaded with `window.scrollY === 0`
- **WHEN** the navbar logo is rendered
- **THEN** the `<img>` resolves to a height of `56 px` (Tailwind `h-14`)
- **AND** the `<picture>` `<source srcset>` resolves to `static/images/fastjob-logo.webp` and the fallback `<img src>` resolves to `static/images/fastjob-logo.png`
- **AND** the wrapper reserves layout space via `aspect-ratio: 1226 / 450` (or an equivalent fixed-height container)
- **AND** the `<img>` carries `alt="FastJob"`

#### Scenario: Navbar logo shrinks smoothly when the navbar enters its scrolled state
- **GIVEN** the page is at the top with the logo at `h-14`
- **WHEN** the user scrolls past the 8 px threshold and the `<nav>` gains `data-scrolled="true"`
- **THEN** the logo `<img>` height transitions to `44 px` (Tailwind `h-11`) within ≤ 200 ms
- **AND** the wrapper's `aspect-ratio` reservation keeps the layout shift score at `0` during the transition
- **AND** the wordmark is not distorted (width follows the 1226 : 450 intrinsic ratio at the new height)

#### Scenario: Reduced-motion users see the size change instantly
- **GIVEN** a user with `prefers-reduced-motion: reduce`
- **WHEN** they scroll past or back over the 8 px threshold
- **THEN** the logo height swaps between `56 px` and `44 px` without any CSS transition

#### Scenario: Favicon is wired in <head>
- **WHEN** any page that extends `base.html` is rendered
- **THEN** the `<head>` contains a `<link rel="icon" href="…favicon.ico">` and a `<link rel="icon" type="image/png" href="…favicon.png">`

#### Scenario: Auth/email-landing logo sizes are unaffected
- **WHEN** `/accounts/login/`, `/accounts/logout/`, `/unsubscribe/<token>/` or any mailing landing card is rendered
- **THEN** the card-level logo continues to use `h-14 w-auto`, exactly as currently rendered in `templates/account/login.html`
- **AND** no sticky-state attribute affects that logo
