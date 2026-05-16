# pricing delta

## ADDED Requirements

### Requirement: Tiered pricing card visual hierarchy
`templates/payments/packages.html` SHALL render its package options in a responsive card grid using `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6`. Every card SHALL use the shared card chrome (`bg-white border border-brand-muted rounded-2xl shadow-sm p-6 sm:p-8`). One card MAY be marked as "recommended" via a ribbon using `bg-brand-dark text-white` and a slightly elevated shadow (`shadow-lg`) — when present, the ribbon MUST contain exactly the Spanish label `Recomendado`. The price per card uses the `text-display` typographic token in `brand.dark`; the unit label uses `text-caption text-brand-ink/70`. Each card's CTA uses the primary-fill button variant. No view-context, pricing, or routing change is introduced — purely visual.

#### Scenario: Pricing grid is responsive across breakpoints
- **WHEN** the packages page is rendered at viewports 320, 640, and 1024 px
- **THEN** the cards are laid out in 1, 2, and 3 columns respectively
- **AND** no card overflows horizontally at 320 px
- **AND** every card retains the same card chrome (`rounded-2xl`, `border-brand-muted`)

#### Scenario: Recommended tier is visually distinct
- **GIVEN** a package the view marks as recommended
- **WHEN** the page renders
- **THEN** that card displays a ribbon with `bg-brand-dark text-white` containing the label `Recomendado`
- **AND** the card's shadow is `shadow-lg` (vs `shadow-sm` on the other cards)
- **AND** the per-card CTA still uses primary-fill

### Requirement: Payment success page hero
`templates/payments/success.html` SHALL render a centered hero card on a subtle gradient backdrop (`bg-gradient-to-br from-brand-cyan/15 via-white to-brand/10`). The user's new envíos balance SHALL be the visual hero, rendered with the `text-display` token in `brand.dark`. The existing CTA label `Ir al Panel de Control` (`success.html:19`) MUST be preserved — it MUST NOT be shortened to `Ir al panel` or otherwise re-translated; it SHALL continue to link to `/dashboard/`.

#### Scenario: Success page surfaces the new balance prominently
- **GIVEN** a user who just completed a Stripe checkout
- **WHEN** they land on `/payments/success/`
- **THEN** the new envíos balance renders with the `text-display` size token
- **AND** the color resolves to `brand.dark` (`#003D99`)
- **AND** a single primary-fill CTA labelled exactly `Ir al Panel de Control` points to `/dashboard/`
