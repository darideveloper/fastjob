# ui-shell delta

## MODIFIED Requirements

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

## ADDED Requirements

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
