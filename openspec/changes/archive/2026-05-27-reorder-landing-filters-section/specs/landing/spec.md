## ADDED Requirements

### Requirement: Features section uses a distinct background after company-finder reorder
The "¿Cómo funciona?" features section in `templates/home.html` SHALL use `bg-gray-50` as its background class to maintain visual separation from the company-finder section immediately above it. Since the company-finder section sits directly above the features section (after the reorder), both would otherwise share a white/default background with no visual break between them.

#### Scenario: Features section renders with a light-gray background
- **GIVEN** an anonymous visitor on the home page
- **WHEN** they scroll past the company-finder section to the features section
- **THEN** the features `<section>` element has the `bg-gray-50` class
- **AND** there is a visible contrast between the white company-finder background and the light-gray features background

## MODIFIED Requirements

### Requirement: Public Company-Finder Section on Landing Page

The public landing page SHALL include a section, positioned **immediately below the hero section**, that lets anonymous visitors explore the company database by sector and location. The section MUST be 100% functional without authentication. It MUST consist of two searchable dropdown widgets (sector and location) and a live counter showing the number of matching companies. The widgets' option lists MUST be sourced from the same allowed-options whitelist as the dashboard. The counter MUST display only an integer and MUST NOT expose any company name, email, primary key, or other row-level data anywhere in the rendered HTML or JavaScript.

When the section's backing API requests fail (rate limit `429`, server error, or network failure), the section MUST degrade gracefully and visibly: it MUST NOT silently render empty, non-functional dropdowns. The visitor MUST be shown a recoverable error state with a retry affordance.

#### Scenario: Anonymous visitor sees the section without logging in

- **GIVEN** a visitor with no authenticated session
- **WHEN** they load the landing page
- **THEN** the company-finder section is rendered immediately below the hero section, with both dropdowns populated and a placeholder counter

#### Scenario: Dropdown options match the current database

- **GIVEN** the `Company` table contains the distinct non-empty areas `{"Tecnología", "Diseño"}`
- **WHEN** an anonymous visitor opens the area dropdown on the landing page
- **THEN** the dropdown lists exactly those two values (alphabetically sorted)
- **AND** the visitor cannot enter a value not in the list and have it accepted

#### Scenario: Counter updates when filters change

- **GIVEN** the visitor has selected `area="Tecnología"` and `location=""`
- **WHEN** the visitor selects `location="Madrid"` from the second dropdown
- **THEN** the counter re-fetches from the public count endpoint
- **AND** the displayed integer reflects the new combined filter

#### Scenario: Section never exposes company-identifying data

- **WHEN** the landing page is rendered with any combination of filter selections
- **THEN** the rendered HTML and the JSON responses fetched by the section's JavaScript contain only label strings (the option lists) and an integer count
- **AND** no company email, name, primary key, or row-level field appears in any DOM node or network response

#### Scenario: Section drives traffic to the pricing page

- **GIVEN** the visitor has used the finder and seen a non-zero count
- **WHEN** they click the section's "Ver paquetes" call-to-action
- **THEN** they navigate to `/payments/paquetes/` (the pricing page)

#### Scenario: Per-IP rate limit applies the same as the dashboard

- **WHEN** a single real client IP exceeds the configured per-hour threshold on the public count endpoint
- **THEN** subsequent counter updates from that IP receive `429 Too Many Requests`
- **AND** the counter degrades gracefully (shows a dash or last-known value rather than crashing)
- **AND** other visitors behind the same reverse proxy are unaffected, because the limit is keyed on the resolved real client IP

#### Scenario: Option-list failure shows a recoverable error instead of empty dropdowns

- **GIVEN** the `GET /api/companies/filter-options/` request fails (e.g. `429` or a server error)
- **WHEN** the landing-page company-finder section initialises
- **THEN** the section displays a visible error message with a retry control
- **AND** it does NOT render silently empty, non-functional dropdowns
- **AND** activating the retry control re-fetches the options and, on success, renders the populated widgets

### Requirement: Landing page renders a pricing-teaser section at the bottom

The public landing page SHALL render a "Paquetes" section as its **final** in-content section, positioned above the page footer. The section MUST iterate the same active `CreditPackage` rows surfaced by `apps/payments/views.py:packages()`, ordered by `price_eur`, and MUST use card chrome visually identical to `templates/payments/packages.html` so a visitor scrolling the landing sees the same pricing surface they would see on `/payments/paquetes/`.

Card markup is extracted into a shared partial `templates/payments/_package_card.html` used by both the landing page and the canonical pricing page. The landing CTAs use the **same auth-gated behavior** as `/payments/paquetes/`: anonymous users see a login-redirect link (`/accounts/login/?next=/payments/paquetes/`), authenticated users POST to Stripe checkout (`{% url 'create_checkout' package.pk %}`). The landing and pricing pages now render identical card chrome and behavior via a single shared partial.

#### Scenario: Pricing teaser appears as the last in-content section

- **GIVEN** at least one active `CreditPackage` row in the database
- **WHEN** an anonymous or authenticated visitor loads `/`
- **THEN** the rendered HTML contains a `<section>` with `id="paquetes"` placed after the trust-signals section and before the page footer
- **AND** that section renders one card per active package, ordered by `price_eur` ascending

#### Scenario: Cards reuse the canonical pricing chrome

- **WHEN** the landing pricing teaser renders
- **THEN** each card's classes resolve to `bg-white`, `rounded-2xl`, `border-brand-muted`, and `p-6` (matching `templates/payments/packages.html`)
- **AND** the recommended card (currently the second card) carries `shadow-lg` and `ring-2 ring-brand-dark` plus a ribbon with the label `Más popular`

#### Scenario: Landing CTAs use the same auth-gated behavior as /payments/paquetes/

- **GIVEN** an **authenticated** user with `is_authenticated = True`
- **WHEN** they load `/`
- **THEN** every CTA inside the pricing teaser is a `<form method="post" action="/payments/create-checkout/...">` (same as the canonical pricing page)
- **GIVEN** an **anonymous** visitor
- **WHEN** they load `/`
- **THEN** every CTA inside the pricing teaser is an `<a>` whose `href` starts with `/accounts/login/?next=/payments/paquetes/` (matching `/payments/paquetes/` anonymous behavior)

#### Scenario: Teaser hides cleanly when no packages exist

- **GIVEN** zero active `CreditPackage` rows
- **WHEN** the landing page renders
- **THEN** the `#paquetes` section is either omitted entirely or shows a neutral "Próximamente disponibles" placeholder — it MUST NOT show an empty 3-column grid skeleton