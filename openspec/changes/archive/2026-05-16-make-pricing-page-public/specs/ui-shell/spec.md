## MODIFIED Requirements

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
