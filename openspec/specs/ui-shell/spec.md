# ui-shell Specification

## Purpose
TBD - created by archiving change add-mobile-responsive-layout. Update Purpose after archive.
## Requirements
### Requirement: Mobile-collapsing global navbar
The global navbar in `templates/base.html` SHALL collapse its right-hand link cluster (and envíos chip, when authenticated) behind a single hamburger toggle button on viewports below the `md` breakpoint (768 px). On viewports `≥ md`, the existing horizontal layout MUST be preserved unchanged. The hamburger button MUST be a real `<button>` (not a checkbox hack), MUST expose `aria-controls` and `aria-expanded`, and MUST be reachable by keyboard.

The anonymous nav cluster (both desktop `md+` and mobile drawer) MUST include a "Paquetes" text link pointing to `/payments/paquetes/`, placed before the "Iniciar sesión" link. The link MUST use the same styling as the other ghost nav links (`text-sm font-medium text-gray-700 hover:text-brand`).

#### Scenario: Authenticated mobile user opens the drawer
- **GIVEN** a logged-in user with 50 envíos at viewport 375 × 667
- **WHEN** the user clicks the hamburger toggle button
- **THEN** a drawer becomes visible containing the user email, the envíos chip, "Panel", "Comprar", and "Salir" stacked vertically
- **AND** `aria-expanded` on the toggle is set to `"true"`

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

#### Scenario: Desktop layout unchanged at md+
- **GIVEN** any viewport `≥ md` (768 px and above)
- **WHEN** any page that extends `base.html` is rendered
- **THEN** the hamburger toggle button has `display: none`
- **AND** the right-hand cluster renders horizontally with the same DOM order and Tailwind classes as before this change, extended only by the new "Paquetes" link in the anonymous branch

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

The logo MUST be rendered inside a `<picture>` element with a WebP `<source>` and a PNG `<img>` fallback. Because the source asset is **1226 × 450** (aspect ratio ≈ 2.72 : 1), the markup MUST NOT specify mismatched `width`/`height` attributes (which would distort the wordmark). Instead, the `<img>` MUST anchor only its rendered height via the Tailwind class `h-9 w-auto` (navbar) or `h-12 w-auto` (auth-card and email-landing card) and let the width follow the intrinsic ratio. The wrapper element MUST carry `style="aspect-ratio: 1226 / 450"` (or an equivalent reserved size) so no CLS occurs while the asset loads. The `<img>` MUST have `alt="FastJob"`. The same logo asset MUST be re-used by `account/login.html`, `account/logout.html`, the socialaccount templates, and the unauthenticated email-landing cards (`mailing/cv_not_found.html`, `mailing/cv_revoked.html`, `mailing/unsubscribe.html`, `mailing/unsubscribe_confirm.html`).

#### Scenario: Navbar logo loads the real brand asset with correct aspect ratio
- **WHEN** any page that extends `base.html` is rendered
- **THEN** the navbar contains a `<picture>` element whose `<source srcset>` resolves to `static/images/fastjob-logo.webp` and whose fallback `<img src>` resolves to `static/images/fastjob-logo.png`
- **AND** the `<img>` carries `class="h-9 w-auto"` (or another `h-* w-auto` pairing that anchors height and lets width follow the 2.72 : 1 intrinsic ratio)
- **AND** the wrapper element reserves layout space via `aspect-ratio: 1226 / 450` (or an equivalent fixed-height container)
- **AND** the `<img>` carries `alt="FastJob"`
- **AND** no inline `<svg>` wordmark remains in the navbar

#### Scenario: Favicon is wired in <head>
- **WHEN** any page that extends `base.html` is rendered
- **THEN** the `<head>` contains a `<link rel="icon" href="…favicon.ico">` and a `<link rel="icon" type="image/png" href="…favicon.png">`

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

