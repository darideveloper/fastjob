# mailing delta

## ADDED Requirements

### Requirement: Unauthenticated email-landing card chrome
The templates `mailing/cv_not_found.html`, `mailing/cv_revoked.html`, `mailing/unsubscribe.html`, and `mailing/unsubscribe_confirm.html` SHALL each render a single centered card on the `brand.bg` page background, using the shared card chrome (`bg-white border border-brand-muted rounded-2xl shadow-sm p-6 sm:p-8`), centered with `mx-auto`, capped at `max-w-md` below `lg` and `max-w-lg` at `lg`+. The FastJob logo (`<picture>` referencing `static/images/fastjob-logo.{webp,png}`, classes `h-12 w-auto`, the wrapper carrying `aspect-ratio: 1226 / 450`) SHALL appear above the card title.

Because these screens are reached from email links by visitors who arrived for a single transactional purpose, the rendered navbar MUST suppress all authenticated-only items (Panel, Comprar, Salir, envíos chip) **even when `user.is_authenticated`** — a visitor who happens to be logged in another tab should still see only the brand logo and (optionally) the anonymous "Iniciar sesión" / "Empezar gratis" links. Implementation MAY achieve this by introducing a `{% block navbar %}` override slot in `base.html` that these four templates blank out or replace with a minimal logo-only navbar, or by switching these templates to a new minimal base template — either is acceptable; the requirement is on the rendered output.

No behavior or routing requirement from the existing `mailing` spec is modified.

#### Scenario: Email-landing screen suppresses authenticated navigation
- **GIVEN** a visitor whose session is authenticated in another tab
- **WHEN** they follow an email link to `/cv/<invalid-token>/` and `mailing/cv_not_found.html` renders
- **THEN** the rendered HTML contains the FastJob logo
- **AND** the rendered HTML does NOT contain a link to `/dashboard/`, `/payments/paquetes/`, `/accounts/logout/`, or the envíos chip
- **AND** the visitor's authenticated session is NOT invalidated by viewing this page (no logout side-effect)

#### Scenario: All four mailing email-landing screens share the card chrome
- **WHEN** each of `mailing/cv_not_found.html`, `mailing/cv_revoked.html`, `mailing/unsubscribe.html`, and `mailing/unsubscribe_confirm.html` is rendered
- **THEN** each page renders a single centered card whose classes resolve to `bg-white`, `border-brand-muted`, `rounded-2xl`, `shadow-sm`
- **AND** each renders the FastJob logo above the title with `h-12 w-auto`

### Requirement: Unsubscribe confirm-prompt CTA is brand-primary, not red
The "Confirmar baja" button on `mailing/unsubscribe_confirm.html` (the GET prompt page rendered by `apps/mailing/views.py:97`) SHALL use the primary-fill button variant (`bg-brand text-white hover:bg-brand-dark`) — NOT a destructive red variant (the current `bg-red-600 hover:bg-red-700` at `unsubscribe_confirm.html:18` MUST be replaced). The intent is to make the unsubscribe action clear and trustworthy rather than adversarial; semantic red is reserved for true destructive intent (e.g. delete account). The masked email being unsubscribed SHALL be rendered in `text-brand-ink font-semibold` so the visitor can clearly confirm which address is being removed. No behavior change to the unsubscribe POST handler is introduced.

#### Scenario: Unsubscribe-prompt button uses primary-fill, not red
- **GIVEN** a visitor following an unsubscribe email link
- **WHEN** `mailing/unsubscribe_confirm.html` is rendered for a valid token (GET)
- **THEN** the `Confirmar baja` `<button type="submit">` has classes resolving to `brand.DEFAULT` background and `brand.dark` hover
- **AND** no element on the page uses `bg-red-*` or `text-red-*` utility classes
- **AND** the masked email rendered at `unsubscribe_confirm.html:13` is shown in `brand.ink` with `font-semibold`

### Requirement: Unsubscribe result page provides a "Volver a FastJob" CTA
`mailing/unsubscribe.html` (the POST result page rendered by `apps/mailing/views.py:119`) SHALL retain its existing confirmation copy `Has cancelado la suscripción` and SHALL add a single ghost-style CTA labelled `Volver a FastJob` linking to `/`. The page currently has no CTA; visitors who finish the unsubscribe flow today reach a dead-end card. The new CTA gives them a graceful exit without re-engaging them in marketing or campaign flows.

#### Scenario: Unsubscribe result page offers a return link
- **GIVEN** a visitor who just submitted the unsubscribe confirmation
- **WHEN** `mailing/unsubscribe.html` renders the POST result
- **THEN** the rendered HTML contains the existing heading `Has cancelado la suscripción`
- **AND** a single `<a href="/">` link labelled `Volver a FastJob` is present, styled as a ghost button (`text-brand-dark hover:bg-brand-muted`)
- **AND** the success affordance is conveyed via `brand.dark` / `brand.DEFAULT`, not exclusively via `text-green-*`
