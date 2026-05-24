## MODIFIED Requirements

### Requirement: Footer renders a scalable social-links cluster
The footer in `templates/base.html` SHALL render a cluster of social-network links sourced from a template-iterable collection (e.g. a `social_links` context variable supplied by a context processor, or an inline `{% with %}` list). The data shape per entry MUST include `name`, `url`, `aria_label`, and `svg` (inline SVG markup) so adding a new social network later is a one-line list addition — never a copy-paste of footer markup.

The initial collection MUST contain exactly one entry: Instagram, pointing to `https://instagram.com/joinfastjob`, with `aria_label="FastJob en Instagram"`.

Each social link MUST:
- be rendered as an `<a>` with `target="_blank"` and `rel="noopener"`,
- carry the `aria-label` from the entry (not visible text),
- contain a 24 × 24 inline SVG using `fill="currentColor"` so it inherits the link color,
- use the same hover treatment as the legal links (`text-gray-500 hover:text-brand transition`).

The cluster MUST NOT break the footer's existing layout: at `< sm`, the copyright, social cluster, and legal-links cluster stack vertically; at `sm+`, the copyright text sits on the left, and the social-links cluster is grouped with the legal links on the right.

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

#### Scenario: Social links are right-aligned with legal links on desktop
- **GIVEN** an anonymous visitor at viewport 1280 × 800
- **WHEN** the footer renders
- **THEN** the copyright text sits alone on the left side of the footer
- **AND** the Instagram icon and legal links ("Privacidad", "Términos", "Contacto") appear in the same horizontal group on the right side
- **AND** the Instagram icon's horizontal centre is to the right of `window.innerWidth / 2`
