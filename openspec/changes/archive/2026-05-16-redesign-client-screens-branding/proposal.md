# Change: Redesign all client-facing screens and adopt a new "Electric Tech" brand palette

## Why

The current FastJob UI relies on an Indigo-based palette (defined at `templates/base.html:8-29`) and a placeholder inline SVG as the wordmark. Two needs have converged:

1. **Brand evolution.** Stakeholders have approved a new, more tech-forward palette (Electric Cyan + Vibrant Blue + Deep Cobalt on near-white, anchored by Dark Slate) and a real logo now lives at `static/images/fastjob-logo.{png,webp}` with matching `favicon.{ico,png}`. Today's templates do not reference either asset.
2. **UX maturity.** End-user screens have grown organically across six template families (`home.html`, `account/`, `dashboard/`, `payments/`, `mailing/`, `socialaccount/`, `404.html`, `500.html`). They share a navbar but diverge in spacing, button styles, empty-state language, form affordances, and mobile behavior. The recent `add-mobile-responsive-layout` change fixed overflow, but the visual system is still inconsistent. A coordinated redesign — done together with the rebrand — avoids paying the QA cost twice.

This proposal rebrands and polishes every screen the **final user** (not staff/admin) can reach, while keeping the codebase architecture untouched (still Django templates + Tailwind CDN, no new dependencies).

## What Changes

### Brand foundation
- **Centralize the new palette** in `templates/base.html`'s Tailwind `theme.extend.colors` block:
  - `brand.bg`      = `#FEFEFE` (page background — replaces today's `bg-gray-50`)
  - `brand.cyan`    = `#00E5FF` (Electric Cyan — accents, focus rings, hover halos, decorative gradients)
  - `brand.DEFAULT` = `#007BFF` (Vibrant Blue — primary CTAs, links, key UI affordances)
  - `brand.dark`    = `#003D99` (Deep Cobalt — hover/active state for primary, headings on light surfaces)
  - `brand.ink`     = `#1A1A1A` (Dark Slate — body text, high-emphasis labels)
  - Plus derived **semantic tokens**:
    - `brand.soft`  = `rgba(0,229,255,0.12)` — subtle tint *background* on white.
    - `brand.muted` = `rgba(0,123,255,0.08)` — card hover / zebra *background* on white.
    - `brand.cloud` = `#E6F2FF` — **light text** on a dark brand backdrop (e.g. hero subtitle, footer caption on the immersive hero). This token is **new** and replaces the current dual-use of `text-brand-muted` as light text. The apply stage MUST migrate the one existing `text-brand-muted` reference in `templates/home.html:17` to `text-brand-cloud`.
    - `brand.ring`  = `#00E5FF` — solid color used by `focus:ring-brand-ring`. The visible contrast on focus comes from the 3 px outline + 2 px offset against the underlying button fill (cobalt or white).
- **Replace the inline placeholder SVG wordmark** in the navbar and footer with the real `static/images/fastjob-logo.webp` (with `.png` fallback via `<picture>`) and a sensible `width/height` to avoid CLS.
- **Wire the favicon**: add `<link rel="icon" href="{% static 'images/favicon.ico' %}">` and `<link rel="icon" type="image/png" href="{% static 'images/favicon.png' %}">` in `base.html`'s `<head>`.
- Introduce a **typographic scale** (`text-display`, `text-h1`, `text-h2`, `text-body`, `text-caption`) so screens stop hand-rolling sizes per page. Inter stays as the font stack.

### Accessibility & responsiveness invariants
- All text/background combinations MUST meet WCAG **AA contrast** (≥ 4.5:1 for body, ≥ 3:1 for large text & UI components). Because Electric Cyan on white fails AA, cyan is **never** used as a CTA fill or body text color — only as an accent/border/focus state, optionally paired with Cobalt fills.
- Every screen MUST pass the existing `ui-shell` "no horizontal overflow" invariant at 320, 360, 375, 414, 768, 1024, 1440 px.
- Every interactive element MUST have a **visible focus ring** using `brand.ring` (3 px outline, 2 px offset).
- Touch targets MUST be ≥ 44 × 44 px on viewports `< md`.

### Per-screen redesigns (visual restyle — UX patterns preserved where they encode meaning)
- **`home.html` (landing)** — The hero **keeps its immersive dark treatment** (current pattern is `bg-gradient-to-br from-brand to-brand-dark text-white`); the rebrand swaps the stops to `from-brand via-brand-dark to-brand-cyan/40` so the gradient now reads as Vibrant-Blue → Deep-Cobalt with an Electric-Cyan glow accent, body copy stays white, subtitle uses `text-brand-cloud`. The dual OAuth CTAs keep their current shape (Google = white fill + vendor icon + `text-brand-dark`; Microsoft = translucent dark fill + vendor icon + `text-white` with a `border-brand-cyan/40`). The company-finder section (rendered *below* the immersive hero, on `brand.bg`) gains a card with a `border-brand-muted` accent border, the "Cómo funciona" steps adopt `bg-brand-soft` icon halos with `text-brand` glyphs. Existing `landing` requirements (envíos terminology, 320 px CTA single-line + `px-6 py-3 text-base` / `px-8 py-4 text-lg` padding pattern, public finder behavior) are **preserved verbatim**.
- **`account/login.html`** — Centered card on near-white, the FastJob logo above the title, OAuth provider buttons get vendor-correct icon + brand-blue border on hover (not cyan fill, to preserve Google/Microsoft trust signals).
- **`account/logout.html`** — Same card chrome as login; the "Cerrar sesión" confirm button uses `brand` fill, cancel uses ghost style.
- **`socialaccount/*.html` (authentication_error, login_cancelled, connections, signup)** — Adopt the same card chrome; error states use a Cobalt icon + slate body (no red unless truly an error).
- **`dashboard/index.html`** — **Structural layout is preserved** (the page already runs a `lg:grid-cols-3` grid with a `col-span-1` left rail and a `col-span-2` activity table; reflowing it would compress the activity table's `min-w-[640px]` and create the very horizontal-overflow we're hardening against). The rebrand restyles in place: every panel migrates `border-gray-100` → `border-brand-muted`, the stats grid's `text-brand` numbers stay, the "Actualizar búsqueda" submit moves from `bg-gray-900` to `bg-brand`, the pause-reason banner keeps its semantic amber/red. **Campaign toggle pattern is preserved**: it remains two distinct status-color buttons (`bg-red-500` "Pausar campaña" when active; `bg-green-500` "Iniciar campaña" when inactive) because red/green encodes start/stop affordance universally — only the focus-ring color is brought into the brand system (`focus:ring-brand-ring`). All form inputs adopt a unified treatment: `border-brand-muted rounded-lg focus:ring-2 focus:ring-brand-ring focus:border-brand`.
- **`dashboard/delete_account.html`** — Stays a warning surface (semantic red is retained for destructive intent) but adopts the new card chrome and typography.
- **`payments/packages.html`** — Card grid (1/2/3 cols at `sm`/`md`/`lg`), the recommended tier is highlighted with a Cobalt ribbon, prices use the new display scale, the CTA per card uses the primary blue fill. Existing envíos-vs-créditos terminology must be respected.
- **`payments/success.html`** — Centered celebration card with a subtle cyan radial gradient, the new envíos balance is the visual hero, the primary CTA preserves the existing label `Ir al Panel de Control` linking to `/dashboard/`.
- **`mailing/cv_not_found.html` / `cv_revoked.html`** — Email-landing cards. The standard anonymous navbar (logo + "Iniciar sesión" / "Empezar gratis") is retained — visitors *might* be unauthenticated or might be logged in another tab; either way, the requirement is that **authenticated-only items (Panel, Comprar, Salir, envíos chip) MUST NOT appear on these pages even if `user.is_authenticated`**, because the visitor arrived from an email link and the page should feel like a transactional landing, not a return-to-dashboard prompt. Card chrome below the navbar holds the FastJob logo + short copy + a single "Ir a FastJob" link to `/`.
- **`mailing/unsubscribe_confirm.html`** *(the GET prompt page — `apps/mailing/views.py:97`)* — Card chrome with masked email shown in `text-brand-ink font-semibold`; the "Confirmar baja" submit button uses the **primary-fill** variant (`bg-brand text-white hover:bg-brand-dark`), not red, because unsubscribing is a legitimate transactional action and red signals destructive/adversarial intent.
- **`mailing/unsubscribe.html`** *(the POST result page — `apps/mailing/views.py:119`)* — Card chrome confirming `Has cancelado la suscripción`, with a single ghost-style CTA `Volver a FastJob` linking to `/`.
- **`404.html` / `500.html`** — Already required by `ui-shell` to use the global navbar/footer. Re-style the centered card to the new palette and add a "Volver al inicio" primary CTA.

### What is explicitly out of scope
- Django admin (`/admin/`) — staff-only, not a "final user" screen.
- Email body templates under `templates/emails/` — outbound deliverability content, separate concern.
- Token-protected CV download response itself (it's a file response, not a screen).
- No new third-party JS, no new CDN dependency, no swap away from Tailwind CDN, no new fonts beyond what `Inter` already covers.
- No behavior or routing changes: every form posts to the same URL, every CTA links to the same target, every view returns the same context.

## Impact

- **Affected specs** (capability deltas in this proposal):
  - `ui-shell` — MODIFY "Centralized Brand Identity" to encode the new palette tokens and logo asset wiring; ADD "Accessible color usage" and "Logo & favicon wiring" requirements.
  - `landing` — MODIFY hero CTA + finder section visual requirements while preserving the existing "envíos terminology", "320 px single-line CTA", and "public company-finder" requirements byte-for-byte at the behavior level.
  - `dashboard` — ADD "Two-column dashboard layout" and "Unified form-control styling" requirements (visual-only, no behavior change).
  - `pricing` — ADD "Tiered pricing card visual hierarchy" requirement (visual-only).
  - `accounts` — ADD "Unified auth-card chrome" requirement covering login/logout and socialaccount error/connection screens.
  - `mailing` — ADD "Unauthenticated email-landing card chrome" requirement covering `cv_not_found`, `cv_revoked`, `unsubscribe`, `unsubscribe_confirm` (visual-only; the existing unsubscribe behavior requirements in `mailing` spec are NOT touched).

- **Affected code** (no edits in this proposal — listed for the apply stage):
  - `templates/base.html` (color tokens, logo `<picture>`, favicon links, typographic scale)
  - `templates/home.html`
  - `templates/account/login.html`, `templates/account/logout.html`
  - `templates/socialaccount/{authentication_error,login_cancelled,connections,signup}.html`
  - `templates/dashboard/{index,delete_account}.html`
  - `templates/payments/{packages,success}.html`
  - `templates/mailing/{cv_not_found,cv_revoked,unsubscribe,unsubscribe_confirm}.html`
  - `templates/404.html`, `templates/500.html`
  - `static/images/` already contains `fastjob-logo.{png,webp}`, `favicon.{ico,png}` — no new asset uploads required.

- **No backend impact**: no views, models, URLs, settings, migrations, Celery tasks, or env vars change. Risk is contained to presentation.

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Electric Cyan on white fails WCAG AA (~1.4:1 contrast). | Cyan is restricted to accent/border/focus-ring/gradient-stop usage; CTA fills and body text use Vibrant Blue (4.6:1) or Deep Cobalt (10.4:1) or Dark Slate (16:1). Spec encodes this. |
| Tailwind CDN cannot statically scan custom utilities. | Continue using arbitrary-value classes (`bg-brand`, `text-brand-ink`) declared in the inline `tailwind.config` block — already the project's pattern. |
| Logo asset is `1226 × 450` (≈ 2.72 : 1). Hardcoding mismatched dimensions would distort the wordmark. | Use only `width=` in the markup (e.g. `width="120"` for navbar, `width="160"` for auth/email cards), pair with CSS `height: auto`, and rely on the asset's intrinsic ratio. Where Tailwind utility classes are preferred, use `h-11 w-auto` (navbar, ≈ 44 px tall) and `h-14 w-auto` (auth/email card, ≈ 56 px tall) so the rendered height anchors the layout and width follows the asset's ratio. The reserved space is computed via `aspect-ratio: 1226 / 450` on the `<picture>` to prevent CLS. |
| Replacing the inline SVG wordmark with a raster image could cause CLS or break print. | Use `<picture>` with the strategy above, `loading="eager"` for the navbar logo, and a fixed `aspect-ratio` on the wrapper so the brand row never reflows. |
| Renaming `brand.muted` semantically would break the one existing `text-brand-muted` usage in `home.html:17`. | Introduce a new `brand.cloud = #E6F2FF` token for light-text-on-dark and migrate that single reference. Tasks 1.x and 2.x cover both the token addition and the migration. |
| Hero "inversion" surprise: the current hero is dark-immersive; without an explicit decision, a redesign could silently flip it to a light backdrop. | This proposal explicitly **preserves the dark-immersive treatment**, only restyling the gradient stops and the CTAs to the new palette. Reviewers wanting a light hero must file a follow-up. |
| Visual regressions on screens not covered by tests. | The proposal does not change behavior — existing pytest suite still passes. Validation is via manual viewport checklist at 320/375/768/1024/1440 px, codified in `tasks.md`. |
| Rebrand drift: a future hex code sneaks back into a template. | The MODIFIED `ui-shell` "Centralized Brand Identity" requirement keeps the prohibition on hardcoded hex codes and on legacy palette names (`indigo-*`) in app templates, while explicitly permitting neutral grays (`gray-*`) and semantic status colors (`red-*`, `green-*`, `amber-*`, `yellow-*`) where they encode status meaning. |
