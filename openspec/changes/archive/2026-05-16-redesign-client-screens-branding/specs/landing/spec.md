# landing delta

## ADDED Requirements

### Requirement: Landing hero adopts the new brand palette while preserving its immersive treatment
The hero `<section>` of `templates/home.html` SHALL keep its existing **dark-immersive** treatment (a brand-colored gradient backdrop with white body text). The gradient stops MUST be updated from the current `from-brand to-brand-dark` to `from-brand via-brand-dark to-brand-cyan/40` so the hero now reads as Vibrant Blue → Deep Cobalt with an Electric Cyan glow accent on the bottom-right. The headline MUST use the `text-display` typographic token (or its breakpoint-stepped fallback) in `text-white`. The subtitle MUST use `text-brand-cloud` — never `text-brand-muted` (which is a transparent tint suitable only for backgrounds) and never `text-brand-cyan` (insufficient contrast against the Cobalt midpoint).

The two OAuth CTAs MUST preserve their existing visual hierarchy: "Empezar con Google" is the **white-fill** primary (currently `bg-white text-indigo-700`, migrated to `bg-white text-brand-dark`) and "Empezar con Microsoft" is the **translucent-dark** secondary (currently `bg-indigo-900/50 … border-indigo-400 text-white`, migrated to `bg-brand-dark/60 hover:bg-brand-dark/80 text-white border border-brand-cyan/40`). The existing 320 px single-line constraint and the `px-6 py-3 text-base` (below `sm`) / `px-8 py-4 text-lg` (`sm` and above) padding pattern from the prior `landing` spec requirements MUST be preserved verbatim.

#### Scenario: Hero keeps immersive dark treatment with new palette
- **WHEN** the home page is rendered
- **THEN** the hero `<section>` element resolves to a CSS `linear-gradient` whose stops include `brand.DEFAULT` (`#007BFF`), `brand.dark` (`#003D99`), and a `brand.cyan` (`#00E5FF`) stop at ≤ 40 % alpha
- **AND** the body text on the hero is white
- **AND** the headline uses the `text-display` font-size token (declared in `templates/base.html`) or its stepped fallback

#### Scenario: Hero subtitle uses brand.cloud, not brand.muted
- **WHEN** the home page is rendered
- **THEN** the subtitle paragraph beneath the hero headline uses `text-brand-cloud` (resolving to `#E6F2FF`)
- **AND** `text-brand-muted` does NOT appear on the subtitle element

#### Scenario: Hero CTAs preserve hierarchy and single-line behavior
- **WHEN** the home page is rendered at viewport 320 × 568
- **THEN** the "Empezar con Google" CTA has `bg-white` and `text-brand-dark` (replacing the prior `text-indigo-700`)
- **AND** the "Empezar con Microsoft" CTA has a translucent Cobalt fill (`bg-brand-dark/60`) and a `border-brand-cyan/40`
- **AND** both CTAs occupy a single line within their button at 320 px (preserving the prior `landing` requirement)
- **AND** the padding pattern `px-6 py-3 text-base` below `sm` / `px-8 py-4 text-lg` at `sm+` is preserved

### Requirement: Company-finder section adopts the new card chrome
The public company-finder section in `templates/home.html` SHALL be wrapped in a card surface using `bg-white border border-brand-muted rounded-2xl shadow-sm`, the live counter chip SHALL use `bg-brand-soft text-brand-dark font-semibold`, and the section's CTA "Ver paquetes y empezar" SHALL use the primary-fill button variant (`bg-brand hover:bg-brand-dark text-white`). All existing behavior requirements from the `landing` spec (allowed-options whitelist, no row-level data exposure, rate limit, target URL `/payments/paquetes/`, single-line-at-320 px) MUST continue to hold.

#### Scenario: Finder card uses new chrome without regressing behavior
- **GIVEN** an anonymous visitor on the home page
- **WHEN** the page is rendered
- **THEN** the finder section is wrapped in an element whose classes resolve to `bg-white`, `border-brand-muted`, `rounded-2xl`, and `shadow-sm`
- **AND** the live counter chip's classes resolve to `bg-brand-soft` background and `brand.dark` text
- **AND** the rendered HTML and any JSON fetched still contain only label strings and an integer count (no row-level data) — the prior `landing` privacy invariant is preserved

#### Scenario: "Cómo funciona" steps consume brand tokens consistently
- **WHEN** the home page is rendered
- **THEN** each of the four step-icon halos uses a `bg-brand-soft` or `bg-brand-muted` background and a `text-brand` glyph
- **AND** no `indigo-*` legacy class survives in this section
