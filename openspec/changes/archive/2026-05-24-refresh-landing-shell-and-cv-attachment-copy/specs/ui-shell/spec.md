# ui-shell Spec Delta — refresh-landing-shell-and-cv-attachment-copy

## ADDED Requirements

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

The initial collection MUST contain exactly one entry: Instagram, pointing to `https://instagram.com/joinfastjob`, with `aria_label="FastJob en Instagram"`.

Each social link MUST:
- be rendered as an `<a>` with `target="_blank"` and `rel="noopener"`,
- carry the `aria-label` from the entry (not visible text),
- contain a 24 × 24 inline SVG using `fill="currentColor"` so it inherits the link color,
- use the same hover treatment as the legal links (`text-gray-500 hover:text-brand transition`).

The cluster MUST NOT break the footer's existing layout: at `< sm`, the copyright, social cluster, and legal-links cluster stack vertically; at `sm+`, copyright sits on the left, the social cluster in the middle, and legal links on the right.

#### Scenario: Instagram link renders with accessible markup
- **WHEN** any page that extends `base.html` is rendered
- **THEN** the footer contains exactly one `<a>` whose `href` is `https://instagram.com/joinfastjob`
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

## MODIFIED Requirements

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
