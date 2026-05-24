# landing Spec Delta — refresh-landing-shell-and-cv-attachment-copy

## ADDED Requirements

### Requirement: Landing page reflects the CV-attachment delivery model
The public landing page (`templates/home.html`) SHALL describe the product as sending the CV **as a PDF attachment**, not as a download link. The strings `enlace de descarga`, `enlaces de descarga`, and `Sin adjuntos` MUST NOT appear in the rendered HTML of `/` after this change. The replacement copy MUST stay accurate to the delivery flow established by `apps/mailing/migrations/0008_auto_20260514_0522.py` (the CV ships as a PDF attached to the outbound email).

#### Scenario: Hero subtitle describes attachment delivery, not link delivery
- **GIVEN** an anonymous visitor at any viewport
- **WHEN** they request `GET /` and the response body is rendered
- **THEN** the hero subtitle paragraph contains the substring `PDF adjunto` (or `en adjunto`)
- **AND** a case-insensitive regex search of the rendered HTML for `enlaces? de descarga` returns zero matches

#### Scenario: Trust-signal card no longer claims "Sin adjuntos"
- **WHEN** the landing page renders the deliverability trust-signal grid
- **THEN** no card on that grid contains the heading `Sin adjuntos`
- **AND** the card that previously carried that heading now describes the PDF-attachment behavior in a positive frame (e.g. `CV en PDF adjunto`)

### Requirement: Landing page renders a pricing-teaser section at the bottom
The public landing page SHALL render a "Paquetes" section as its **final** in-content section, positioned immediately below the existing company-finder section and above the page footer. The section MUST iterate the same active `CreditPackage` rows surfaced by `apps/payments/views.py:packages()`, ordered by `price_eur`, and MUST use card chrome visually identical to `templates/payments/packages.html` so a visitor scrolling the landing sees the same pricing surface they would see on `/payments/paquetes/`.

Card markup is extracted into a shared partial `templates/payments/_package_card.html` used by both the landing page and the canonical pricing page. The landing CTAs use the **same auth-gated behavior** as `/payments/paquetes/`: anonymous users see a login-redirect link (`/accounts/login/?next=/payments/paquetes/`), authenticated users POST to Stripe checkout (`{% url 'create_checkout' package.pk %}`). The landing and pricing pages now render identical card chrome and behavior via a single shared partial.

#### Scenario: Pricing teaser appears as the last in-content section
- **GIVEN** at least one active `CreditPackage` row in the database
- **WHEN** an anonymous or authenticated visitor loads `/`
- **THEN** the rendered HTML contains a `<section>` with `id="paquetes"` placed after the company-finder section and before the page footer
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

### Requirement: Landing-page error pages and cv-link templates use neutral copy
Templates rendered by the legacy `cv_download` view (`templates/mailing/cv_not_found.html`, `templates/mailing/cv_revoked.html`) SHALL use copy that does NOT reference "enlace de descarga" or "descarga revocada". The view itself remains operational so historical email links keep resolving; only the rendered strings change.

#### Scenario: cv_not_found page uses neutral phrasing
- **WHEN** a client requests `GET /cv/<unknown-token>/` and the `cv_not_found.html` template renders
- **THEN** the rendered HTML does NOT contain the substring `enlace de descarga`
- **AND** the subtitle paragraph reads `Este enlace ya no está disponible o ha expirado.`

#### Scenario: cv_revoked page uses neutral phrasing
- **WHEN** a client follows a link whose `MailingLog` has been revoked and `cv_revoked.html` renders
- **THEN** the `<title>` reads `Enlace revocado — FastJob` (not `Descarga revocada — FastJob`)
- **AND** the subtitle paragraph reads `Este enlace ya no está disponible porque el destinatario ha cancelado la suscripción.`
- **AND** neither the heading nor the body contains the substring `La descarga ya no está disponible`

## MODIFIED Requirements

### Requirement: Landing page uses "envíos" terminology for the per-CV unit
The public landing page (`templates/home.html`) SHALL refer to the
purchasable unit-of-value as `envío` / `envíos` (singular / plural,
matching Spanish grammar) in every user-visible string. The legacy term
`crédito` / `créditos` MUST NOT appear anywhere in the rendered HTML of
the landing page (including, but not limited to: section headings,
taglines, button labels, and the "How it works" step list). The landing
page SHALL also avoid the strings `enlace de descarga` / `enlaces de
descarga` (see also the new `Landing page reflects the CV-attachment
delivery model` requirement above): the product now ships the CV as a
PDF attachment, so any link-based phrasing is factually wrong. When a
sentence relies on the contrast between the two terms (e.g. the current
"Cada crédito equivale a un envío"), it MUST be reworded so it remains
meaningful under the new vocabulary rather than becoming tautological.

#### Scenario: Landing page rendered to an anonymous visitor contains no "crédito" text
- **GIVEN** a visitor with no authenticated session
- **WHEN** they request `GET /` and the response body is rendered
- **THEN** a case-insensitive regex search of the rendered HTML for
  `cr[ée]dito` returns zero matches
- **AND** the "How it works" step labelled `3.` reads `3. Compra envíos`
  (not `3. Compra créditos`)

#### Scenario: The reworded tagline reads naturally
- **WHEN** the landing page renders the tagline immediately below the
  `3. Compra envíos` heading
- **THEN** the tagline text is
  `Cada envío manda tu CV a una empresa. Elige el paquete que mejor se adapte a ti.`
- **AND** the rendered sentence does NOT contain the substring
  `equivale a un envío` (the previous tautology-prone phrasing)

#### Scenario: Pre-existing "envío" usage on the landing page is preserved
- **GIVEN** the existing copy at `templates/home.html` line ~99
  ("Asunto y cuerpo aleatorios en cada envío…")
- **WHEN** the landing page renders after the change
- **THEN** that sentence is unchanged
- **AND** the noun "envío" is used consistently across both the
  pricing-step copy and the deliverability copy
