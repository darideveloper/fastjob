# ui-shell Specification

## Purpose
TBD - created by archiving change add-mobile-responsive-layout. Update Purpose after archive.
## Requirements
### Requirement: Mobile-collapsing global navbar
The global navbar in `templates/base.html` SHALL collapse its right-hand link cluster (and envíos chip, when authenticated) behind a single hamburger toggle button on viewports below the `md` breakpoint (768 px). On viewports `≥ md`, the existing horizontal layout MUST be preserved unchanged. The hamburger button MUST be a real `<button>` (not a checkbox hack), MUST expose `aria-controls` and `aria-expanded`, and MUST be reachable by keyboard.

#### Scenario: Authenticated mobile user opens the drawer
- **GIVEN** a logged-in user with 50 envíos at viewport 375 × 667
- **WHEN** the user clicks the hamburger toggle button
- **THEN** a drawer becomes visible containing the user email, the envíos chip, "Panel", "Comprar", and "Salir" stacked vertically
- **AND** `aria-expanded` on the toggle is set to `"true"`

#### Scenario: Anonymous mobile visitor opens the drawer
- **GIVEN** an anonymous visitor at viewport 320 × 568
- **WHEN** the visitor clicks the hamburger toggle button
- **THEN** a drawer becomes visible containing "Iniciar sesión" and "Empezar gratis" stacked vertically
- **AND** the FastJob logo and the toggle button do not overlap

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
- **AND** the right-hand cluster renders horizontally exactly as it does today (same DOM order, same Tailwind classes, byte-identical to the pre-change `<nav>` `outerHTML` excluding only the new collapse-related siblings)

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
`templates/base.html` SHALL define the project's brand identity (colors, fonts, and core spacing) within its Tailwind configuration block. Every server-rendered page MUST inherit these settings via template extension. Direct usage of hex codes or hardcoded color classes (e.g., `text-[#4F46E5]`) in app templates is DISCOURAGED in favor of the centralized theme aliases.

#### Scenario: Global color update
- **GIVEN** a requirement to change the brand color from Indigo to Emerald
- **WHEN** the `brand.DEFAULT` value is updated in `templates/base.html`
- **THEN** every page (Home, Dashboard, Login, Logout, 404, etc.) MUST reflect the new color on its interactive elements and accents without further template modifications.

#### Scenario: Error pages follow the global layout
- **GIVEN** a user encounters a 404 or 500 error
- **WHEN** the error template is rendered
- **THEN** it MUST include the standard FastJob navbar and footer
- **AND** the content MUST be centered in a responsive card matching the brand aesthetic.

