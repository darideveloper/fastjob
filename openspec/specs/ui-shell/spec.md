# ui-shell Specification

## Purpose
TBD - created by archiving change add-mobile-responsive-layout. Update Purpose after archive.
## Requirements
### Requirement: Mobile-collapsing global navbar
The global navbar in `templates/base.html` SHALL collapse its right-hand link cluster (and envíos chip, when authenticated) behind a single hamburger toggle button on viewports below the `md` breakpoint (768 px). On viewports `≥ md`, the existing horizontal layout MUST be preserved unchanged in **structure**; only the authenticated dashboard link's **label** and **breakpoint behavior of the user-email span** change as described below. The hamburger button MUST be a real `<button>` (not a checkbox hack), MUST expose `aria-controls` and `aria-expanded`, and MUST be reachable by keyboard.

The anonymous nav cluster (both desktop `md+` and mobile drawer) MUST include a "Paquetes" text link pointing to `/payments/paquetes/`, placed before the "Iniciar sesión" link. The link MUST use the same styling as the other ghost nav links (`text-sm font-medium text-gray-700 hover:text-brand`).

The authenticated nav cluster (both desktop `md+` and mobile drawer) SHALL label the dashboard link as `Panel de envíos` (not the previous `Panel`). On the desktop cluster, that link MUST carry `whitespace-nowrap` so the longer label never wraps when the row is dense. To keep the desktop row single-line at `md` (768 px) where the envíos chip + longer label + Comprar + Salir already crowd the right cluster, the `{{ user.email }}` span MUST be hidden until `lg+` (its class moves from `hidden sm:block` to `hidden lg:block`).

#### Scenario: Authenticated mobile user opens the drawer
- **GIVEN** a logged-in user with 50 envíos at viewport 375 × 667
- **WHEN** the user clicks the hamburger toggle button
- **THEN** a drawer becomes visible containing the user email, the envíos chip, "Panel de envíos", "Comprar", and "Salir" stacked vertically
- **AND** `aria-expanded` on the toggle is set to `"true"`

#### Scenario: Authenticated desktop user sees the new label
- **GIVEN** a logged-in user at viewport 1280 × 800
- **WHEN** any page that extends `base.html` is rendered
- **THEN** the right-hand cluster contains a link with the visible text `Panel de envíos` (not `Panel`)
- **AND** that link's class list contains `whitespace-nowrap`
- **AND** the row renders on a single horizontal line with no overflow

#### Scenario: User email is hidden at md to preserve single-line layout
- **GIVEN** a logged-in user at viewport 768 × 1024 (exact `md` breakpoint)
- **WHEN** the page renders
- **THEN** the `{{ user.email }}` span has computed `display: none`
- **AND** the visible cluster (envíos chip, "Panel de envíos", "Comprar", "Salir") fits in one row
- **AND** at viewport 1024 × 800 (`lg`) the email span is again visible
- **NOTE (explicit trade-off):** the email is intentionally hidden across the full `md` range (768 px through 1023 px, ≈ 256 px of viewport). This is an accepted compromise — the longer "Panel de envíos" label combined with the envíos chip + Comprar + Salir cannot fit on a single line at that breakpoint without losing something. The email reappears at `lg` (1024 px) where the row has enough room. If a future iteration wants the email visible earlier, the alternative is to hide "Comprar" until `lg+` and move it into the drawer at `md`.

#### Scenario: Anonymous mobile visitor opens the drawer
- **GIVEN** an anonymous visitor at viewport 320 × 568
- **WHEN** the visitor clicks the hamburger toggle button
- **THEN** a drawer becomes visible containing "Paquetes", "Iniciar sesión", and "Empezar gratis" stacked vertically
- **AND** the FastJob logo and the toggle button do not overlap

#### Scenario: Anonymous desktop visitor sees the pricing link
- **GIVEN** an anonymous visitor at viewport ≥ md (768 px)
- **WHEN** any page that extends `base.html` is rendered
- **THEN** the right-hand desktop cluster contains a link labelled "Paquetes" with `href="/payments/paquetes/"`
- **AND** it appears before the "Iniciar sesión" link
- **AND** it uses the ghost link style (`text-sm font-medium text-gray-700 hover:text-brand`)

#### Scenario: Drawer closes on outside click
- **GIVEN** the drawer is open at any viewport `< md`
- **WHEN** the user clicks anywhere outside the drawer (and outside the toggle button)
- **THEN** the drawer's `hidden` class is reapplied
- **AND** `aria-expanded` on the toggle is set to `"false"`

#### Scenario: Drawer closes on Escape
- **GIVEN** the drawer is open and focus is anywhere within the drawer or on the toggle
- **WHEN** the user presses the `Escape` key
- **THEN** the drawer is hidden
- **AND** focus returns to the toggle button

#### Scenario: Desktop layout unchanged at md+ (modulo this change's two edits)
- **GIVEN** any viewport `≥ md` (768 px and above)
- **WHEN** any page that extends `base.html` is rendered
- **THEN** the hamburger toggle button has `display: none`
- **AND** the right-hand cluster renders horizontally with the same DOM order as before this change
- **AND** the only intentional differences from the prior state are: the dashboard link's visible text is `Panel de envíos` with `whitespace-nowrap`, and the email span's breakpoint is `lg+` instead of `sm+`

### Requirement: No horizontal overflow on any page that extends base.html
For every server-rendered page that extends `templates/base.html`, at viewports 320, 360, 375, and 414 px, `document.documentElement.scrollWidth` MUST equal `window.innerWidth`. The audit's measured 421 px overflow on the dashboard at 320 px MUST no longer reproduce.

#### Scenario: Dashboard at 320 px does not overflow horizontally
- **GIVEN** a logged-in user with seeded CVs and mailing logs at viewport 320 × 800
- **WHEN** the dashboard page (`/dashboard/`) is loaded
- **THEN** `document.documentElement.scrollWidth === window.innerWidth` (i.e. 320 === 320)
- **AND** no element on the page has a `getBoundingClientRect().right` greater than 320

#### Scenario: Anonymous landing at 375 px does not overflow horizontally
- **GIVEN** an anonymous visitor at viewport 375 × 667
- **WHEN** the home page (`/`) is loaded
- **THEN** `document.documentElement.scrollWidth === 375`

#### Scenario: Pages other than home and dashboard inherit the same invariant
- **GIVEN** an anonymous visitor at viewport 320 × 568
- **WHEN** they visit each of `/payments/paquetes/`, `/accounts/login/`, `/cv/no-disponible/`, and any unsubscribe URL that renders `templates/mailing/unsubscribe.html`
- **THEN** for every such page, `document.documentElement.scrollWidth === 320`

### Requirement: Drawer JS does not depend on a third-party framework
The hamburger toggle interaction MUST be implemented in inline vanilla JavaScript embedded in `templates/base.html` (or a single `static/js/navbar.js` module loaded on every page). It MUST NOT introduce a new third-party CDN dependency (no Alpine.js, no jQuery, no headless-ui port). This preserves the trusted-origin posture established by the C3 hardening referenced in `config/urls.py`.

#### Scenario: No new external <script src> is added
- **WHEN** the rendered HTML of any page that extends `base.html` is inspected
- **THEN** the only third-party `<script src=…>` tags present are those that already exist before this change (Tailwind CDN; combobox.js stays first-party)

#### Scenario: The toggle works without JavaScript frameworks loaded
- **GIVEN** a browser with all third-party origins blocked except the FastJob origin
- **WHEN** the user opens the dashboard at viewport 320 × 800 and clicks the hamburger toggle
- **THEN** the drawer opens normally
- **AND** clicking outside or pressing Escape closes it

### Requirement: Centralized Brand Identity
`templates/base.html` SHALL define the project's brand identity (colors, fonts, typographic scale, and core spacing) within its Tailwind configuration block. Every server-rendered page MUST inherit these settings via template extension.

The brand palette MUST be:

- `brand.bg`      = `#FEFEFE` (page background)
- `brand.ink`     = `#1A1A1A` (body text)
- `brand.DEFAULT` = `#007BFF` (primary CTA, links)
- `brand.dark`    = `#003D99` (primary hover/active, headings)
- `brand.cyan`    = `#00E5FF` (accent only — borders, focus rings, decorative gradient stops)
- `brand.soft`    = `rgba(0,229,255,0.12)` (tinted info **backgrounds**)
- `brand.muted`   = `rgba(0,123,255,0.08)` (card hover **background**, zebra, panel borders)
- `brand.cloud`   = `#E6F2FF` (**light text on dark brand backdrop**, e.g. hero subtitle)
- `brand.ring`    = `#00E5FF` for the `focus:ring` utility

The font stack MUST remain `Inter, ui-sans-serif, system-ui, -apple-system, sans-serif`. The `fontSize` extension MUST expose tokens `display`, `h1`, `h2`, `body`, `caption` so app templates consume `text-display` / `text-h1` / etc. rather than hand-rolled sizes.

**Color-source rules in app templates** (templates other than `base.html` itself):

1. Hardcoded hex codes are PROHIBITED, **except** inside vendor SVG icon `<path fill="…">` attributes (the Google "G" and Microsoft squares carry vendor-specified colors and MUST not be re-skinned).
2. Legacy brand palette names from the previous identity (`indigo-*`, `text-indigo-*`, `bg-indigo-*`, `border-indigo-*`) are PROHIBITED — every such reference MUST be migrated to a `brand.*` token.
3. Neutral grays (`text-gray-*`, `bg-gray-*`, `border-gray-*`) ARE PERMITTED for non-primary text, dividers, and chrome where they don't carry brand meaning.
4. Semantic status colors (`red-*`, `green-*`, `amber-*`, `yellow-*`) ARE PERMITTED **only where they encode status meaning** — e.g. the campaign toggle's start/stop buttons, the pause-reason banner, the danger-zone delete-account CTA, the activity log's "Enviado"/"Fallido" chips.

#### Scenario: Global color update propagates everywhere
- **GIVEN** a stakeholder later changes `brand.DEFAULT` to a different blue in `templates/base.html`
- **WHEN** every server-rendered final-user page is re-rendered
- **THEN** every primary CTA, link, and focus-ring color reflects the new value
- **AND** no app template needs to be edited

#### Scenario: No hardcoded hex codes and no legacy palette names in app templates
- **GIVEN** the codebase post-change
- **WHEN** `rg -n "#[0-9A-Fa-f]{3,6}" templates/ | rg -v 'path fill='` is run (excluding `templates/base.html` and vendor SVG icon fills)
- **THEN** zero matches are returned
- **AND** `rg -n "indigo-" templates/` returns zero matches

#### Scenario: Semantic status colors are still permitted where meaningful
- **WHEN** the dashboard is rendered with an active campaign
- **THEN** the "Pausar campaña" button continues to use `bg-red-500 hover:bg-red-600` (red = stop affordance, semantically appropriate)
- **AND** the "Enviado"/"Fallido" chips in the recent-activity table continue to use `bg-green-50 text-green-700` / `bg-red-50 text-red-700`
- **AND** this usage does NOT violate the no-hex / no-legacy-palette rule

#### Scenario: Error pages follow the global layout
- **GIVEN** a user encounters a 404 or 500 error
- **WHEN** the error template is rendered
- **THEN** it MUST extend `base.html` (inheriting the navbar, footer, palette, and typographic scale)
- **AND** the content MUST be centered in a responsive card matching the brand aesthetic
- **AND** a primary CTA labelled `Volver al inicio` MUST link to `/`

### Requirement: Accessible color usage
Every text/background pair rendered on a final-user screen MUST meet WCAG **AA** contrast: ≥ 4.5 : 1 for body text and ≥ 3 : 1 for large text (≥ 18 pt regular or ≥ 14 pt bold) and non-text UI components. Because `brand.cyan` (`#00E5FF`) produces only ~1.4 : 1 contrast on `brand.bg`, it MUST NOT be used as:

- the `text-` color of any rendered text on a light background,
- the `bg-` fill of an interactive surface (button, link, toggle, input),
- the sole visual signal for a state change.

`brand.cyan` MAY appear as:

- a 1–2 px border (`border-brand-cyan`) on a card or chip,
- a focus outline via `focus:ring-brand-ring`,
- a stop in a gradient whose *other* stop is `brand.dark`, `brand.DEFAULT`, or `brand.ink`,
- a decorative halo on hover, paired with a high-contrast underlying surface.

Light text on a dark brand backdrop MUST use `brand.cloud` (`#E6F2FF`) — not `brand.cyan`, not `brand.muted` — so that subtitle and caption text on the immersive landing hero passes AA (≥ 9 : 1 against `brand.dark`).

Primary CTA fills MUST use `brand.DEFAULT` with `text-white` (4.8 : 1 ✅) and `hover:bg-brand-dark` (10.4 : 1 ✅).

#### Scenario: Cyan never fills an interactive surface
- **GIVEN** the templates after this change
- **WHEN** `rg -n "bg-brand-cyan|text-brand-cyan" templates/` is run
- **THEN** every match is either inside a `gradient-*` utility, inside a `border-*` utility, inside a `ring-*` / `focus:ring-*` utility, or inside a decorative element that has no interactive role and no rendered text content

#### Scenario: Hero subtitle uses brand.cloud, not brand.muted
- **GIVEN** the home page after this change
- **WHEN** the subtitle paragraph under the hero headline is inspected
- **THEN** it uses `text-brand-cloud` (resolving to `#E6F2FF`), not `text-brand-muted`
- **AND** its contrast against the underlying gradient stops `brand.DEFAULT` / `brand.dark` is ≥ 4.5 : 1

#### Scenario: Primary CTA passes AA against white text
- **GIVEN** any primary CTA on any final-user screen
- **WHEN** its computed `background-color` and the white text on it are measured
- **THEN** the contrast ratio is ≥ 4.5 : 1
- **AND** on `:hover` the background darkens to `brand.dark` and the ratio is ≥ 7 : 1

#### Scenario: Visible focus ring on every interactive element
- **GIVEN** a keyboard user tabs through any final-user screen
- **WHEN** focus lands on any `<a>`, `<button>`, `<input>`, `<select>`, or `<textarea>`
- **THEN** a visible outline using `brand.ring` is rendered with at least 2 px offset from the element edge
- **AND** the outline contrast against the adjacent background is ≥ 3 : 1

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

### Requirement: Responsive design invariants for final-user screens
Every final-user screen (the landing page, auth screens, dashboard, payment screens, mailing email-landing screens, and error pages) MUST render without horizontal overflow at viewport widths 320, 360, 375, 414, 768, 1024, and 1440 px (extending the existing "no horizontal overflow" invariant beyond just home and dashboard). On viewports `< md` (768 px), every interactive control (button, link styled as a button, toggle, form input) MUST have a hit area of at least 44 × 44 CSS pixels.

**Exception:** the recent-activity `<table>` on `dashboard/index.html` carries `min-w-[640px]` to keep four columns readable; its horizontal scroll is contained by a wrapping `overflow-x-auto` block whose `getBoundingClientRect().right` MUST still equal `window.innerWidth`. The outer page MUST NOT scroll horizontally even when the inner table does.

#### Scenario: Every final-user screen passes the outer-overflow check
- **GIVEN** an anonymous or authenticated user at viewports 320, 360, 375, 414, 768, 1024, and 1440 px
- **WHEN** they load any of `/`, `/dashboard/`, `/accounts/login/`, `/accounts/logout/`, `/accounts/3rdparty/`, `/payments/paquetes/`, `/payments/success/`, `/cv/<token>/` (in its error states), `/unsubscribe/<token>/` GET, `/unsubscribe/<token>/` POST result, and any 404 or 500 page
- **THEN** for every such page and viewport, `document.documentElement.scrollWidth === window.innerWidth`

#### Scenario: Inner table scroll does not break outer-page invariant
- **GIVEN** an authenticated user on `/dashboard/` at viewport 375 × 800 with seeded mailing logs
- **WHEN** the recent-activity table renders inside its `overflow-x-auto` wrapper
- **THEN** the wrapper element scrolls horizontally to expose all four columns
- **AND** `document.documentElement.scrollWidth === 375` (the outer page does not scroll)

#### Scenario: Touch targets are ≥ 44 px below md
- **GIVEN** a viewport `< md`
- **WHEN** any final-user screen is rendered
- **THEN** every `<button>`, every primary-CTA `<a>`, and every form `<input>` has a `getBoundingClientRect()` height ≥ 44 and width ≥ 44

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

### Requirement: Global container max-width is 1536 px (max-w-screen-2xl)
Every user-facing template that extends `templates/base.html` (including `base.html` itself) SHALL constrain its outer container to Tailwind's `max-w-screen-2xl` (1536 px). The legacy `max-w-7xl` token (1280 px) MUST NOT appear in any user-facing template after this change. This widens the comfortable reading column by ~20 % on large monitors while preserving the existing responsive padding (`px-4 sm:px-6 lg:px-8`).

#### Scenario: No user-facing template uses the old max-w-7xl token
- **WHEN** `rg -n 'max-w-7xl' templates/` is run after the change
- **THEN** zero matches are returned

#### Scenario: Pages render wider on large monitors
- **GIVEN** an anonymous or authenticated user at viewport 1920 × 1080
- **WHEN** any page that extends `base.html` is loaded
- **THEN** the outer container's `getBoundingClientRect().width` equals `1536` (`max-w-screen-2xl` resolved)
- **AND** at viewport 1280 × 800 the container width equals `1280` minus the lateral padding (the page does not over-stretch on smaller desktops because the max-width cap is non-binding below 1536 px)

#### Scenario: Wider container preserves the no-horizontal-overflow invariant
- **GIVEN** any user-facing page after the change
- **WHEN** the page is loaded at viewports 320, 360, 375, 414, 768, 1024, 1440, and 1920 px
- **THEN** `document.documentElement.scrollWidth === window.innerWidth` at every viewport
- **AND** the `Responsive design invariants for final-user screens` requirement continues to hold

### Requirement: Footer renders a scalable social-links cluster
The footer in `templates/base.html` SHALL render a cluster of social-network links sourced from a template-iterable collection (e.g. a `social_links` context variable supplied by a context processor, or an inline `{% with %}` list). The data shape per entry MUST include `name`, `url`, `aria_label`, and `svg` (inline SVG markup) so adding a new social network later is a one-line list addition — never a copy-paste of footer markup.

The initial collection MUST contain exactly one entry: Instagram, pointing to `https://www.instagram.com/fastjob.es`, with `aria_label="FastJob en Instagram"`.

Each social link MUST:
- be rendered as an `<a>` with `target="_blank"` and `rel="noopener"`,
- carry the `aria-label` from the entry (not visible text),
- contain a 24 × 24 inline SVG using `fill="currentColor"` so it inherits the link color,
- use the same hover treatment as the legal links (`text-gray-500 hover:text-brand transition`).

The cluster MUST NOT break the footer's existing layout: at `< sm`, the copyright, social cluster, and legal-links cluster stack vertically; at `sm+`, the copyright text sits on the left, and the social-links cluster is grouped with the legal links on the right.

#### Scenario: Instagram link renders with accessible markup
- **WHEN** any page that extends `base.html` is rendered
- **THEN** the footer contains exactly one `<a>` whose `href` is `https://www.instagram.com/fastjob.es`
- **AND** that anchor carries `aria-label="FastJob en Instagram"`, `target="_blank"`, and `rel` containing `noopener`
- **AND** it contains an inline `<svg>` with `width="24"` and `height="24"` whose paths use `fill="currentColor"`

#### Scenario: Adding a new social is a one-line change
- **GIVEN** a future change appending a TikTok entry to `social_links`
- **WHEN** the templates and footer are inspected
- **THEN** no additional `<a>` markup needs to be added to `base.html` — the new social renders solely from the new list entry through the existing `{% for %}` loop

#### Scenario: Footer layout survives the new cluster on mobile
- **GIVEN** an anonymous visitor at viewport 320 × 568
- **WHEN** the footer renders
- **THEN** `document.documentElement.scrollWidth === 320` (no horizontal overflow)
- **AND** the copyright line, the social cluster, and the legal-links cluster are stacked vertically (the existing `flex flex-col sm:flex-row` parent is preserved)

#### Scenario: Social links are right-aligned with legal links on desktop
- **GIVEN** an anonymous visitor at viewport 1280 × 800
- **WHEN** the footer renders
- **THEN** the copyright text sits alone on the left side of the footer
- **AND** the Instagram icon and legal links ("Privacidad", "Términos", "Contacto") appear in the same horizontal group on the right side
- **AND** the Instagram icon's horizontal centre is to the right of `window.innerWidth / 2`

### Requirement: Scroll-Reveal Animation System

All final-user pages that extend `templates/base.html` SHALL support a scroll-reveal animation system implemented as a zero-dependency IntersectionObserver script embedded in `base.html` and a companion CSS file `static/css/reveal.css`. Elements marked with `data-reveal` SHALL start invisible (`opacity: 0 !important; transform: translateY(1.5rem) !important`) and transition to their natural position when the observer detects they have entered the viewport at 15 % visibility. The `!important` declarations are required to guarantee that the initial hidden state wins over any Tailwind utility classes on the same element, regardless of CSS source order. The observer SHALL remove the `data-reveal` attribute on reveal, apply any `transition-delay` from a `data-reveal-delay` attribute, and then unobserve the element.

For elements inside Django `{% for %}` loops (e.g. pricing cards), the `data-reveal-delay` SHALL use `forloop.counter0` multiplied by a stagger interval defined on a parent wrapper via `data-reveal-stagger` (e.g. `data-reveal-stagger="150"`). The observer script SHALL look for the nearest ancestor with `data-reveal-stagger` and compute the final delay as `value * stagger`.

Users who have enabled `prefers-reduced-motion: reduce` in their OS or browser settings SHALL see all elements rendered in their final state immediately (no opacity transition, no transform shift, no stagger delay), via a `@media (prefers-reduced-motion: reduce)` override in `reveal.css`. This override SHALL also include `transition: none !important` to suppress any inherited or inline transitions that might otherwise produce a visible shift.

The `reveal.css` file SHALL also define a `"slide-down"` reveal variant (`[data-reveal="slide-down"] { transform: translateY(-1.5rem) !important }`) for elements that should appear to slide downward into position (e.g. top banners), and a `"scale-in"` keyframe animation (`0% { transform: scale(0) } 80% { transform: scale(1.1) } 100% { transform: scale(1) }`) for celebratory icons (e.g. the success-page checkmark).

#### Scenario: Element fades and slides up on scroll

- **GIVEN** an element with `data-reveal` and `motion-safe:transition-all motion-safe:duration-700 motion-safe:ease-out` classes exists below the fold
- **WHEN** the user scrolls the element into the viewport (15 % visible)
- **THEN** the `data-reveal` attribute is removed
- **AND** the element transitions from `opacity: 0; transform: translateY(1.5rem)` to `opacity: 1; transform: none` over 700 ms

#### Scenario: Staggered sibling reveals with delay

- **GIVEN** four elements with `data-reveal` and `data-reveal-delay` values `"0"`, `"1"`, `"2"`, `"3"` inside a container with `data-reveal-stagger="100"`
- **WHEN** all four enter the viewport simultaneously
- **THEN** the first element reveals immediately (0 × 100 ms = 0 ms delay)
- **AND** the second, third, and fourth elements begin their transitions 100 ms, 200 ms, and 300 ms after the first respectively (computed as delay × stagger)

#### Scenario: Stagger in Django for-loop with forloop.counter0

- **GIVEN** a Django `{% for package in packages %}` loop where each card has `data-reveal-delay="{{ forloop.counter0 }}"` and the grid wrapper has `data-reveal-stagger="150"`
- **WHEN** three cards enter the viewport simultaneously
- **THEN** the cards reveal with delays of 0 ms, 150 ms, and 300 ms respectively

#### Scenario: Reduced-motion user sees no animation

- **GIVEN** a user whose browser reports `prefers-reduced-motion: reduce`
- **WHEN** any page with `data-reveal` elements is loaded
- **THEN** all elements render at `opacity: 1; transform: none` immediately
- **AND** no transitions are applied (`transition: none !important`)
- **AND** the IntersectionObserver still runs (removing attributes) but no visual transition occurs

#### Scenario: Slide-down banner reveal

- **GIVEN** a conditional banner element with `data-reveal="slide-down"`
- **WHEN** the element enters the viewport
- **THEN** it transitions from `opacity: 0; transform: translateY(-1.5rem)` to `opacity: 1; transform: none`

#### Scenario: No new third-party JavaScript or CSS dependencies

- **WHEN** the rendered HTML of any page extending `base.html` is inspected
- **THEN** the only third-party `<script src=…>` tags are those that existed before this change (Tailwind CDN, combobox.js)
- **AND** no `<script>` tag loads AOS, GSAP, anime.js, or any other animation library

### Requirement: Hover Micro-Interactions on Cards and Icons

Interactive card elements and icon containers across all final-user pages SHALL provide subtle hover feedback using only Tailwind utility classes with the `motion-safe:` prefix. Cards SHALL lift (`hover:-translate-y-0.5` or `hover:-translate-y-1`) and gain enhanced shadow (`hover:shadow-md` or `hover:shadow-lg`) on hover. Icon wrappers inside grouped cards SHALL scale up (`group-hover:scale-110` or `group-hover:scale-125`) on card hover. Arrow icons inside grouped CTA links SHALL shift right (`group-hover:translate-x-1`) on link hover.

All hover transitions SHALL use `motion-safe:transition-all motion-safe:duration-200` (or `motion-safe:duration-150` for icons) and SHALL be suppressed entirely under `prefers-reduced-motion: reduce`.

#### Scenario: Feature card lifts on hover

- **GIVEN** an anonymous visitor on the landing page
- **WHEN** the user hovers over any of the four "Cómo funciona" feature card `<div>` elements
- **THEN** the card visually shifts upward by 1 px (Tailwind `hover:-translate-y-1`) and its shadow increases
- **AND** hovering the card also scales the icon wrapper inside it by 10 %

#### Scenario: Pricing card lifts on hover

- **GIVEN** an anonymous visitor on the pricing page
- **WHEN** the user hovers over any pricing card (including the "Recomendado" card)
- **THEN** the card shifts upward (`hover:-translate-y-1`) and its shadow increases to `shadow-lg`
- **AND** the "Recomendado" ring is preserved during the hover

#### Scenario: Dashboard stat card shows subtle hover

- **GIVEN** an authenticated user on the dashboard
- **WHEN** the user hovers over any of the four stat cards
- **THEN** the card gains `shadow-md` and a subtle border-color shift (`hover:border-brand/20`)
- **AND** no card lifts more than 0.5 rem

#### Scenario: Hover effects respect reduced motion

- **GIVEN** a user whose browser reports `prefers-reduced-motion: reduce`
- **WHEN** they hover over any card or icon with `motion-safe:transition-*` and `hover:*` classes
- **THEN** the hover state change (shadow, color) still occurs instantly
- **AND** no `transform` property is applied (no lift, no scale)

### Requirement: Landing Page Scroll-Reveal Marking

The landing page (`templates/home.html`) SHALL mark the following elements with `data-reveal` (and stagger delays per the design document) so they animate into view on scroll: hero headline, hero subtitle, hero CTA row, Features section heading, each of the four feature cards, Trust section heading, each of the three trust cards, Company Finder section heading, Company Finder subtitle, Company Finder filter card, and Company Finder CTA button. All marked elements SHALL also carry `motion-safe:transition-all motion-safe:duration-700 motion-safe:ease-out` (or `motion-safe:duration-500` for smaller elements) to define the transition timing.

#### Scenario: Hero section reveals in sequence

- **GIVEN** an anonymous visitor scrolls to the landing page
- **WHEN** the hero section enters the viewport
- **THEN** the `<h1>` reveals with 0 ms delay
- **AND** the subtitle `<p>` reveals 100 ms after the headline
- **AND** the CTA button row reveals 200 ms after the headline

#### Scenario: Feature cards stagger on scroll

- **GIVEN** the four "Cómo funciona" feature cards are below the fold
- **WHEN** they scroll into view
- **THEN** each card reveals 100 ms after the previous one (delays of 0, 100, 200, 300 ms)

#### Scenario: Trust cards stagger on scroll

- **GIVEN** the three trust-signal cards are below the fold
- **WHEN** they scroll into view
- **THEN** each card reveals 100 ms after the previous one (delays of 0, 100, 200 ms)

### Requirement: Pricing Page Scroll-Reveal Marking

The pricing page (`templates/payments/packages.html`) SHALL mark the following elements with `data-reveal`: the header (h1 + subtitle container), the pricing grid wrapper with `data-reveal-stagger="150"` so that each pricing card in the `{% for %}` loop can use `data-reveal-delay="{{ forloop.counter0 }}"` to compute stagger delays of 0, 150, and 300 ms, the Stripe trust line, and the social proof line.

#### Scenario: Pricing cards stagger on scroll

- **GIVEN** an anonymous visitor scrolls to the pricing page
- **WHEN** the pricing grid enters the viewport
- **THEN** the first pricing card reveals with 0 ms delay
- **AND** the second pricing card reveals 150 ms later
- **AND** the third pricing card reveals 300 ms later
- **AND** the stagger is computed from `data-reveal-delay="{{ forloop.counter0 }}"` multiplied by the parent's `data-reveal-stagger="150"`

### Requirement: Dashboard Scroll-Reveal Marking

The dashboard page (`templates/dashboard/index.html`) SHALL mark the following elements with `data-reveal`: the pause-reason banner (with `data-reveal="slide-down"` variant), the dashboard header, each of the four stat cards (with stagger delays 0, 100, 200, 300 ms), the CV list card, the filters card, the danger-zone card, and the recent-activity card. Dashboard stat card transitions SHALL use `motion-safe:duration-500` (faster than landing, since the dashboard is functional not marketing).

#### Scenario: Dashboard stat cards stagger on load

- **GIVEN** an authenticated user loads the dashboard
- **WHEN** the page renders
- **THEN** the four stat cards reveal in sequence with 100 ms stagger

#### Scenario: Pause banner slides down

- **GIVEN** an authenticated user whose campaign is paused for a quota reason
- **WHEN** the dashboard renders with the pause banner visible
- **THEN** the banner reveals using the `slide-down` variant (entering from above)

### Requirement: Auth and Status Page Scroll-Reveal Marking

The login page (`templates/account/login.html`) SHALL mark its card container with `data-reveal`. The delete-account page (`templates/dashboard/delete_account.html`) SHALL mark its card container with `data-reveal`. The payment success page (`templates/payments/success.html`) SHALL mark its checkmark icon with the `scale-in` keyframe animation, and its h1, credits number, and CTA button with `data-reveal` at staggered delays (150 ms, 300 ms, 450 ms). The 404 and 500 error pages SHALL mark their card containers with `data-reveal`.

#### Scenario: Success page checkmark bounces in

- **GIVEN** an authenticated user who just completed a payment
- **WHEN** the success page loads
- **THEN** the green checkmark icon plays the `scale-in` keyframe animation
- **AND** the "¡Pago completado!" headline reveals 150 ms after the checkmark
- **AND** the credits number reveals 300 ms after the checkmark
- **AND** the CTA button reveals 450 ms after the checkmark

#### Scenario: Login card fades in

- **GIVEN** an anonymous visitor navigates to `/accounts/login/`
- **WHEN** the page renders
- **THEN** the login card container fades up into view with `duration-500`

#### Scenario: Error page card fades in

- **GIVEN** a visitor encounters a 404 or 500 error
- **WHEN** the error page renders
- **THEN** the centered card container fades up into view

#### Scenario: Delete-account card fades in

- **GIVEN** an authenticated user navigates to `/dashboard/delete-account/`
- **WHEN** the page renders
- **THEN** the danger-zone card container fades up into view with `duration-500`

### Requirement: Footer attribution line
The footer in `templates/base.html` SHALL render a small attribution line immediately below the copyright text, inside the same left-aligned wrapper, reading `Powered by DariDeveloper` where `DariDeveloper` is a hyperlink.

The attribution SHALL:
- use `text-xs text-gray-400` styling (smaller and more muted than the copyright line)
- sit on its own line below the copyright `<span>` with only the natural inline gap (no extra `mt-*` or `mb-*`)
- wrap within the parent container without causing horizontal overflow on any viewport
- render the anchor `<a>` with `href="https://api.whatsapp.com/send?phone=5214493402622"`, `target="_blank"`, and `rel="noopener"`
- inherit the footer's `hover:text-brand transition` on the link (matching other footer links)

The existing footer layout invariant MUST be preserved: at `< sm`, the copyright + attribution stack vertically above the social and legal clusters; at `sm+`, the left group (copyright + attribution + social) sits on the left and the legal links on the right.

#### Scenario: Attribution renders below copyright on every page
- **WHEN** any page that extends `base.html` is rendered
- **THEN** the footer contains a `Powered by DariDeveloper` text node
- **AND** `DariDeveloper` is wrapped in an `<a>` with `href="https://api.whatsapp.com/send?phone=5214493402622"`
- **AND** that anchor carries `target="_blank"` and `rel` containing `noopener`
- **AND** the `<a>` uses `text-gray-400 hover:text-brand transition` styling
- **AND** the attribution line is below the `© … FastJob` copyright text

#### Scenario: Attribution does not break the footer layout at 320 px
- **GIVEN** an anonymous visitor at viewport 320 × 568
- **WHEN** the footer renders
- **THEN** `document.documentElement.scrollWidth === 320` (no horizontal overflow)
- **AND** the attribution text is fully visible (not clipped or overflowing its parent)

#### Scenario: Attribution does not break the footer layout at 1280 px
- **GIVEN** an anonymous visitor at viewport 1280 × 800
- **WHEN** the footer renders
- **THEN** the attribution text sits below the copyright text inside the left group
- **AND** the social-links cluster and legal-links cluster are in their correct positions (left group vs. right group per the existing layout)

### Requirement: Vendored Typed.js and search-suggestion module loaded alongside combobox.js
The Typed.js library and the search-suggestion module SHALL be loaded in the `{% block extra_js %}` of each template that contains a `[data-filter-widget]` — currently `templates/home.html` and `templates/dashboard/index.html`. The scripts SHALL be loaded in this order after `combobox.js`: (1) `static/js/vendor/typed.min.js`, (2) `static/js/search-suggestion.js`.

Loading in the child templates (rather than in `base.html`) ensures `combobox.js` executes first, so the `window.FastJobFilter` namespace (including `optionsPromise` and `readyPromise`) is available before `search-suggestion.js` runs. Pages without a filter widget (login, pricing, etc.) will not load these scripts at all, keeping page weight minimal.

No additional third-party CDN `<script>` tags SHALL be introduced by this change. The vendored Typed.js file is the only new dependency, and it is served from the same origin as the FastJob application (consistent with the "Drawer JS does not depend on a third-party framework" and "Scroll-Reveal Animation System" requirements that prohibit external CDN dependencies).

The `search-suggestion.js` module SHALL:
- Await `window.FastJobFilter.readyPromise` (which resolves only after both `optionsPromise` has resolved AND `initWidgets()` has completed, so combobox containers are fully initialised and `optionsData` is available on the namespace)
- Generate 10 random `"{Area} en {Location}..."` strings from `window.FastJobFilter.optionsData`, capitalising the first letter of each value (since the API returns lowercase names)
- Store a parallel `stringMeta` array mapping each display string to its original lowercase `{area, location}` values for use by the click handler
- Shuffle the generated strings using Typed.js's `shuffle: true` option
- Initialise Typed.js on each `[data-search-suggestion]` element with `typeSpeed: 50`, `backSpeed: 30`, `backDelay: 2000`, `loop: true`, `showCursor: true`
- Attach a click handler that resolves the current string via Typed.js internal state (`typed.sequence[typed.arrayPos]` → `typed.strings[...]`) rather than parsing `el.textContent`, because the displayed text can be mid-word during animation; the handler then looks up the original area/location values from the `stringMeta` array and calls `window.FastJobFilter.addValue()` for each match
- Locate the parent `[data-filter-widget]` via `el.parentElement.querySelector('[data-filter-widget]')` instead of `el.closest()`, because on the landing page the suggestion span is a `<div>` sibling of the widget rather than a descendant
- Attach focus/blur listeners on all combobox text inputs within the same `[data-filter-widget]` to pause/resume the Typed.js instance
- Check `window.matchMedia('(prefers-reduced-motion: reduce)')` at init time; if the media query matches, render a single static string and skip Typed.js initialisation entirely
- Fall back to a static hint (`"Busca por sector y ubicación"`) if the options data has insufficient variety (< 2 areas or < 2 locations) or if the options fetch failed

`combobox.js` SHALL be updated to expose a `window.FastJobFilter` namespace containing four things: (1) `optionsPromise` — a getter returning the memoised fetch promise so `search-suggestion.js` can await it without a duplicate API call, (2) `optionsData` — set to `{areas, locations}` after `initWidgets()` completes, (3) `readyPromise` — a promise that resolves only after all combobox widgets on the page have been initialised (i.e. after `initWidgets()` has completed and each container's `_addValue` is available), and (4) `addValue(widgetElement, comboboxType, value)` — a function that finds the `[data-combobox="<comboboxType>"]` container inside the given widget and calls its internal `addValue` method to programmatically add a selected pill. This avoids exposing the entire IIFE internals; only the four hooks that `search-suggestion.js` needs are made public.

Internally, `combobox.js` SHALL store each initialized combobox's `addValue` function (currently a private closure variable inside `initCombobox`) on the container element — either directly as a property (e.g. `container._addValue = addValue`) or via a `WeakMap` — so that the public `addValue()` helper can look it up by DOM element.

#### Scenario: Typed.js is loaded from the FastJob origin, not from a CDN
- **GIVEN** a page containing a `[data-filter-widget]` (e.g. the landing page or dashboard)
- **WHEN** the page is rendered
- **THEN** the HTML includes a `<script src="/static/js/vendor/typed.min.js">` tag
- **AND** no `<script>` tag references a third-party CDN domain for Typed.js
- **AND** the version comment above the tag identifies the Typed.js version and source URL

#### Scenario: search-suggestion.js is loaded only on pages with filter widgets
- **GIVEN** the landing page or dashboard
- **WHEN** the page is rendered
- **THEN** the HTML includes `<script>` tags in `{% block extra_js %}` in the order: `combobox.js`, `typed.min.js`, `search-suggestion.js`
- **GIVEN** a page without a filter widget (e.g. `/accounts/login/` or `/payments/paquetes/`)
- **WHEN** the page is rendered
- **THEN** neither `typed.min.js` nor `search-suggestion.js` is loaded

#### Scenario: No duplicate API calls from the suggestion module
- **GIVEN** the landing page or dashboard loads
- **WHEN** both `combobox.js` and `search-suggestion.js` initialise
- **THEN** only one HTTP request to `/api/companies/filter-options/` is made
- **AND** `search-suggestion.js` awaits the promise already memoised by `combobox.js`

#### Scenario: Suggestion module waits for combobox initialization
- **GIVEN** the landing page or dashboard loads
- **WHEN** `search-suggestion.js` awaits `window.FastJobFilter.readyPromise`
- **THEN** the promise resolves only after all `[data-combobox]` containers have been initialised and their `_addValue` methods are available on the DOM
- **AND** calling `window.FastJobFilter.addValue(widget, 'area', 'abogados')` after `readyPromise` resolves successfully adds a pill to the area combobox

#### Scenario: Suggestion strings capitalise the first letter of each value
- **GIVEN** the filter-options response returns `areas: ["abogados", "tecnologia"]` and `locations: ["madrid", "barcelona"]`
- **WHEN** `search-suggestion.js` generates suggestion strings
- **THEN** each string has the format `"{CapitalisedArea} en {CapitalisedLocation}..."` (e.g. `"Abogados en Madrid..."`, `"Tecnologia en Barcelona..."`)
- **AND** the values passed to `addValue()` for combobox pre-fill remain lowercase (e.g. `"abogados"`, `"madrid"`) to match the whitelist

#### Scenario: Click handler resolves the correct string via Typed.js internal state, not DOM parsing
- **GIVEN** the suggestion animation is mid-type, displaying `"Aparatos e"` (incomplete fragment of `"Aparatos en Madrid..."`)
- **WHEN** the visitor clicks the suggestion element
- **THEN** the handler reads `typed.sequence[typed.arrayPos]` to get the full `"Aparatos en Madrid..."` string
- **AND** matches `"aparatos"` and `"madrid"` against the whitelist via the `stringMeta` lookup
- **AND** both comboboxes are pre-filled correctly

#### Scenario: Script URLs carry a cache-busting query parameter
- **WHEN** any page containing a `[data-filter-widget]` is rendered
- **THEN** each `{% static %}` script tag in `{% block extra_js %}` has a `?v=N` query parameter (e.g. `combobox.js?v=5`)
- **AND** the three script tags use the same version number for consistency

### Requirement: Footer links MUST point to the legal and contact pages
The footer in `templates/base.html` SHALL provide functional links to the Privacy Policy, Terms of Service, and a direct contact email. The current placeholders (`#`) MUST be replaced with internal URL names or a direct email link.

- "Privacidad" link MUST point to the URL named `privacy`.
- "Términos" link MUST point to the URL named `terms`.
- "Contacto" link MUST point to `mailto:admin@fastjob.es`.

#### Scenario: Footer links are functional
- **WHEN** any page extending `base.html` is rendered
- **THEN** the "Privacidad" link has an `href` attribute resolving to `/privacidad/`
- **AND** the "Términos" link has an `href` attribute resolving to `/terminos/`

#### Scenario: Footer contact link is functional
- **WHEN** any page extending `base.html` is rendered
- **THEN** the "Contacto" link has an `href` attribute resolving to `mailto:admin@fastjob.es`

