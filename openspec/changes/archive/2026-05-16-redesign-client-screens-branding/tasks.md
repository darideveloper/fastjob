# Tasks

## 1. Brand foundation (templates/base.html)
- [x] 1.1 In `templates/base.html`, replace the `tailwind.config.theme.extend.colors.brand.*` block with the new tokens: `bg #FEFEFE`, `ink #1A1A1A`, `DEFAULT #007BFF`, `dark #003D99`, `cyan #00E5FF`, `soft rgba(0,229,255,0.12)`, `muted rgba(0,123,255,0.08)`, `cloud #E6F2FF`, `ring #00E5FF`.
- [x] 1.2 In the same Tailwind config, add the typographic scale `fontSize`: `display`, `h1`, `h2`, `body`, `caption` per `design.md` §2. Verify the CDN parses the `clamp()` tuple form; fall back to stepped breakpoint sizes if not.
- [x] 1.3 Update `<body>` classes: `bg-brand-bg text-brand-ink` (was `bg-gray-50 text-gray-900`).
- [x] 1.4 Replace the inline `<svg>` wordmark in the navbar `<a href="/">` with a `<picture>` element loading `fastjob-logo.webp` + `.png` fallback, classes `h-9 w-auto`, `alt="FastJob"`, `loading="eager"`. Wrap the `<picture>` in a span/div carrying `style="aspect-ratio: 1226 / 450"` to reserve the layout slot and prevent CLS.
- [x] 1.5 Add favicon `<link>` tags in `<head>` pointing to `static/images/favicon.ico` and `favicon.png`.
- [x] 1.6 Audit the navbar's authenticated cluster and mobile drawer; rename every `text-brand-light`/`bg-brand-soft`/`bg-brand-muted` reference that survives to its new semantic meaning, and replace any `bg-gray-100`/`bg-gray-200` *brand-adjacent* surfaces (like the "Salir" button background) with brand tokens. Keep neutral grays on truly-neutral chrome.
- [x] 1.7 Update the `messages` block color classes to use the new palette (info → `bg-brand-soft text-brand-dark border-brand-muted`; keep red/yellow/green semantic).
- [x] 1.8 Verify and measure the PNG/WebP asset weight; if either exceeds ~50 KB, generate a resized export (≥ 2× the 36 px navbar height for retina, i.e. ≥ 72 px tall, preserving 1226 : 450 ratio).

## 2. Landing page (templates/home.html)
- [x] 2.1 Update the hero `<section>` (`templates/home.html:11`): change the gradient from `from-brand to-brand-dark` to `from-brand via-brand-dark to-brand-cyan/40`; keep `text-white` on the body; ensure the headline (currently `text-4xl sm:text-5xl font-extrabold`) uses `text-display` (or the stepped breakpoint fallback if `clamp()` is rejected).
- [x] 2.2 Migrate the hero subtitle at `templates/home.html:17` from `text-brand-muted` to `text-brand-cloud` (the new light-on-dark token). Failure to migrate would make the subtitle nearly invisible.
- [x] 2.3 Restyle the two OAuth hero CTAs while preserving each button's distinct hierarchy: Google = `bg-white text-brand-dark` (was `text-indigo-700`), Microsoft = `bg-brand-dark/60 hover:bg-brand-dark/80 text-white border border-brand-cyan/40` (was `bg-indigo-900/50 … border-indigo-400`). Preserve the existing `px-6 py-3 text-base` (below `sm`) / `px-8 py-4 text-lg` (`sm+`) padding to keep the 320 px single-line behavior from the `landing` spec.
- [x] 2.4 Restyle the public company-finder section card to use `bg-white border border-brand-muted rounded-2xl shadow-sm`; the counter chip uses `bg-brand-soft text-brand-dark`.
- [x] 2.5 Restyle the "Ver paquetes y empezar" CTA to primary fill (`bg-brand text-white hover:bg-brand-dark`); preserve the 320 px single-line behavior and the existing padding pattern.
- [x] 2.6 Restyle the "Cómo funciona" step icons: each circular icon halo at `home.html:40,50,60,70` keeps `bg-brand-muted`/`bg-brand-soft` (already brand tokens) and the glyph stays `text-brand` — semantic is unchanged, only the underlying color values shift with the rebrand.
- [x] 2.7 Re-verify zero horizontal overflow at 320 / 375 / 768 / 1024 / 1440 px.

## 3. Auth screens (templates/account, templates/socialaccount)
- [x] 3.1 `account/login.html`: card chrome is **already present** (line 7: `bg-white rounded-2xl shadow-sm border border-gray-100 p-8`); migrate `border-gray-100` → `border-brand-muted`, add the FastJob logo above the title (`<picture>` with `h-12 w-auto`), keep the two OAuth buttons exactly as they are — they already match the vendor-button rule (white fill, vendor-color icons, slate text, labels `Continuar con Google` / `Continuar con Microsoft`). Do **not** rename the labels.
- [x] 3.2 `account/logout.html`: apply the same card-chrome migration; "Cerrar sesión" button uses primary fill (`bg-brand text-white hover:bg-brand-dark`), "Cancelar" uses ghost style.
- [x] 3.3 `socialaccount/authentication_error.html`: card chrome (`border-brand-muted`), icon uses `text-brand-dark` (not red), body uses `text-brand-ink`, single primary CTA `Volver a iniciar sesión` linking to `/accounts/login/`.
- [x] 3.4 `socialaccount/login_cancelled.html`: card chrome, neutral tone using `text-brand-ink`, primary CTA `Volver a iniciar sesión` linking to `/accounts/login/`.
- [x] 3.5 `socialaccount/connections.html`: card chrome wrapping the connections list; per-provider rows show provider icon + remove button (ghost style).
- [x] 3.6 `socialaccount/signup.html`: card chrome (rarely reached, but must match).

## 4. Dashboard (templates/dashboard)
- [x] 4.1 `dashboard/index.html`: **preserve** the existing `lg:grid-cols-3` layout (line 116) with left rail (`lg:col-span-1`) carrying CVs + Filters + Danger Zone and right area (`lg:col-span-2`) carrying Recent Activity — this is a restyle, not a reflow.
- [x] 4.2 Migrate each panel's chrome: `border-gray-100` → `border-brand-muted`; keep `rounded-2xl shadow-sm`. Section titles (currently `font-bold text-lg`) adopt `text-h2 text-brand-dark`.
- [x] 4.3 Replace ad-hoc form-input classes with a unified utility stack: `border-brand-muted rounded-lg focus:ring-2 focus:ring-brand-ring focus:border-brand`. Apply to the CV-name input (line 157) and the combobox widgets.
- [x] 4.4 Update the "Actualizar búsqueda" submit button (line 217): replace `bg-gray-900 hover:bg-black` with `bg-brand hover:bg-brand-dark`.
- [x] 4.5 **Preserve the campaign toggle's two-button pattern** at the page header (lines 65-78): keep `bg-red-500 hover:bg-red-600` for "Pausar campaña" and `bg-green-500 hover:bg-green-600` for "Iniciar campaña" — red/green encode start/stop affordance universally. Only add `focus:ring-2 focus:ring-brand-ring focus:ring-offset-2` for keyboard visibility. Do NOT change to a switch and do NOT replace with brand-blue.
- [x] 4.6 Stats grid (lines 80-114): keep the 4-card structure and the `text-brand` envíos number; migrate `border-gray-100` → `border-brand-muted` on each card.
- [x] 4.7 Ensure every CV row's action buttons hit the 44 px touch-target minimum at viewports `< md` (add `py-2 px-3` where current buttons render shorter than 44 px).
- [x] 4.8 `dashboard/delete_account.html`: card chrome on a red-toned warning surface; destructive CTA in `bg-red-600`, secondary back to dashboard in ghost.

## 5. Payments (templates/payments)
- [x] 5.1 `payments/packages.html`: card grid (`grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6`); the recommended tier gets a Cobalt ribbon and a slightly elevated shadow.
- [x] 5.2 Each pricing card uses `text-display` for the price, `text-caption` for the unit label, primary-fill CTA per tier.
- [x] 5.3 `payments/success.html`: centered hero card with `bg-gradient-to-br from-brand-cyan/15 via-white to-brand/10` accent; the new envíos balance uses `text-display text-brand-dark`; preserve the existing CTA label `Ir al Panel de Control` (do NOT rename) linking to `/dashboard/`.

## 6. Email-landing screens (templates/mailing)
- [x] 6.1 `mailing/cv_not_found.html`: card chrome (`border-brand-muted`), FastJob logo at top (`<picture>` with `h-12 w-auto`), friendly Spanish copy, single link to `/`.
- [x] 6.2 `mailing/cv_revoked.html`: same chrome as 6.1, different copy explaining the link was revoked.
- [x] 6.3 `mailing/unsubscribe_confirm.html` *(the GET prompt page — `apps/mailing/views.py:97`)*: card chrome, masked email rendered in `text-brand-ink font-semibold` (line 13), replace the existing `bg-red-600 hover:bg-red-700` on the "Confirmar baja" submit button (line 18) with **primary-fill** (`bg-brand hover:bg-brand-dark text-white`) — unsubscribing is transactional, not destructive.
- [x] 6.4 `mailing/unsubscribe.html` *(the POST result page — `apps/mailing/views.py:119`)*: card chrome, retain the "Has cancelado la suscripción" confirmation copy, **add** a single ghost-style CTA `Volver a FastJob` linking to `/` (the page currently has no CTA at all).
- [x] 6.5 For all four mailing email-landing screens: even when `user.is_authenticated`, the rendered navbar MUST NOT show authenticated-only items (Panel, Comprar, Salir, envíos chip). This requires either a `{% block navbar %}{% endblock %}` override in `base.html` that these templates can blank out / replace, or moving these templates to a new minimal base. Pick the lower-impact option during apply.

## 7. Error pages (templates/404.html, 500.html)
- [x] 7.1 `404.html`: extend `base.html`, centered card chrome, `text-display` "404", "Volver al inicio" primary CTA.
- [x] 7.2 `500.html`: same shape, friendly copy, "Volver al inicio" primary CTA.

## 8. Accessibility & responsiveness QA
- [x] 8.1 Run a contrast audit (DevTools or `axe` extension) on every screen listed above; confirm every text/bg pair meets WCAG AA.
- [x] 8.2 Verify no use of `bg-brand-cyan` or `text-brand-cyan` on an interactive surface (`rg "brand-cyan" templates/` and review each match).
- [x] 8.3 Manual responsive check at 320, 375, 768, 1024, 1440 px on each screen — confirm no horizontal overflow per the existing `ui-shell` invariant.
- [x] 8.4 Keyboard pass: every interactive element receives the `brand-ring` focus outline; Tab order is logical; Escape closes the navbar drawer (existing behavior).
- [x] 8.5 Touch-target audit: every button/CTA below `md` is ≥ 44 × 44 px.

## 9. Regression sweep
- [x] 9.1 Run the existing pytest suite (`pytest`) — must remain green (no behavior changes were made).
- [x] 9.2 Grep for hardcoded hex codes in `templates/`, **excluding vendor SVG icon fills**: `rg -n "#[0-9A-Fa-f]{3,6}" templates/ | rg -v 'path fill='`. Only `base.html`'s Tailwind config block should remain in the output.
- [x] 9.3 Grep for legacy palette names that must have been migrated: `rg -n "indigo-" templates/` MUST return zero matches.
- [x] 9.4 Confirm no new `<script src=…>` was added (preserves `ui-shell` "no new framework" requirement).
- [x] 9.5 Confirm `<picture>` and favicon links resolve to existing files in `static/images/`.
- [x] 9.6 Confirm `rg -n "text-brand-muted" templates/` returns zero matches (the one `home.html:17` usage MUST have been migrated to `text-brand-cloud`).

## 10. Validate proposal
- [x] 10.1 Run `openspec validate redesign-client-screens-branding --strict` and resolve any reported issues.
