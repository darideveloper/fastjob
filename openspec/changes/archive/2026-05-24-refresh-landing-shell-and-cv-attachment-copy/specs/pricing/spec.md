# pricing Spec Delta — refresh-landing-shell-and-cv-attachment-copy

## MODIFIED Requirements

### Requirement: Tiered pricing card visual hierarchy
`templates/payments/packages.html` SHALL render its package options in a responsive card grid using `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6`. Every card SHALL use the shared card chrome (`bg-white border border-brand-muted rounded-2xl shadow-sm p-6 sm:p-8`). One card MAY be marked as "most popular" via a ribbon using `bg-brand-dark text-white` and a slightly elevated shadow (`shadow-lg`) — when present, the ribbon MUST contain exactly the Spanish label `Más popular` (replacing the prior `Recomendado` label, which MUST NOT appear in the rendered HTML after this change). The price per card uses the `text-display` typographic token in `brand.dark`; the unit label uses `text-caption text-brand-ink/70`. Each card's CTA uses the primary-fill button variant. The card markup is extracted into a shared partial `templates/payments/_package_card.html` used by both the canonical pricing page and the landing-page pricing teaser, so the card chrome is enforced in one place. No view-context, pricing, or routing change is introduced — purely visual reorganisation.

#### Scenario: Pricing grid is responsive across breakpoints
- **WHEN** the packages page is rendered at viewports 320, 640, and 1024 px
- **THEN** the cards are laid out in 1, 2, and 3 columns respectively
- **AND** no card overflows horizontally at 320 px
- **AND** every card retains the same card chrome (`rounded-2xl`, `border-brand-muted`)

#### Scenario: Most-popular tier is visually distinct and labelled "Más popular"
- **GIVEN** a package the view marks as most-popular (currently the second card)
- **WHEN** the page renders
- **THEN** that card displays a ribbon with `bg-brand-dark text-white` containing exactly the visible text `Más popular`
- **AND** the rendered HTML does NOT contain the prior ribbon string `Recomendado` anywhere in `templates/payments/packages.html`
- **AND** the card's shadow is `shadow-lg` (vs `shadow-sm` on the other cards)
- **AND** the per-card CTA still uses primary-fill

#### Scenario: Landing-page pricing teaser uses the same ribbon label
- **GIVEN** the new landing-page pricing teaser introduced by this change (see `landing` spec delta)
- **WHEN** `/` is rendered with at least two active packages
- **THEN** the recommended card's ribbon on the landing page also reads `Más popular`
- **AND** the literal string `Recomendado` does not appear in the rendered HTML of `/`
