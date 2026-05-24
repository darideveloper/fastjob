# Tasks

## 1. CV-attachment copy alignment (no "enlace de descarga")
- [x] 1.1 Edit `templates/home.html:18` — replace the hero subtitle so it no longer references "enlaces de descarga". Proposed copy: `FastJob usa tu propia cuenta de Gmail o Outlook para enviar tu CV en PDF adjunto, con alta tasa de entrega y plantillas variadas.`
- [x] 1.2 Edit `templates/home.html:87–89` — replace the "Sin adjuntos" trust-signal card. Proposed copy: heading `CV en PDF adjunto`, body `Tu CV viaja como adjunto profesional, listo para que el reclutador lo abra al instante.`
- [x] 1.3 Edit `templates/mailing/cv_not_found.html:31` — replace `Este enlace de descarga ha expirado o no es válido.` with `Este enlace ya no está disponible o ha expirado.` Keep the heading "Enlace no disponible" (it is neutral).
- [x] 1.4 Edit `templates/mailing/cv_revoked.html:3,25,26` — change `{% block title %}` from `Descarga revocada — FastJob` to `Enlace revocado — FastJob`; change `<h1>` from `Este enlace ha sido revocado` (keep) but the subtitle (line 26) from `La descarga ya no está disponible porque el destinatario ha cancelado la suscripción.` to `Este enlace ya no está disponible porque el destinatario ha cancelado la suscripción.`
- [x] 1.5 Grep `rg -in "enlace.{0,12}descarga|descarga.{0,12}revocada"` across `templates/` and `apps/` (excluding `apps/mailing/migrations/`) — confirm zero remaining matches in user-facing files. Document the result.

## 2. Pricing cards section on the landing page
- [x] 2.1 **Replace the bare `TemplateView` at `config/urls.py:46`** (currently `TemplateView.as_view(template_name="home.html")`) with a custom view. Create `apps/core/views.py` (the file does not yet exist) and define `HomeView(TemplateView)` with `template_name = "home.html"` and `get_context_data()` returning:
  - `packages = list(CreditPackage.objects.filter(is_active=True).order_by("price_eur"))`,
  - `successful_sends_count = ...` — mirror **exactly** the computation used in `apps/payments/views.py:packages()` at apply time (note: the peer proposal `update-pricing-cards-copy-and-fake-sends` introduces `displayed_sends_floor` into this computation; if that peer has already shipped, reuse the same `max(real_count, SystemSettings.get().displayed_sends_floor)` expression here so the home teaser and the pricing page show the same number).
  Then update `config/urls.py:46` to `path("", HomeView.as_view(), name="home")` and add the necessary import.
- [x] 2.2 Extract the package card markup from `templates/payments/packages.html` into a shared partial `templates/payments/_package_card.html`. Both `packages.html` and `home.html` now `{% include %}` this partial, passing `package` and `is_popular` per card. The `{% load humanize %}` added during initial implementation was subsequently removed as no humanize filters are used in the template.
- [x] 2.3 Landing pricing CTAs use the same auth-gated behavior as the canonical pricing page: anonymous users see a login redirect link (`/accounts/login/?next=/payments/paquetes/`), authenticated users POST to Stripe checkout (`{% url 'create_checkout' package.pk %}`). This replaced the previous always-`<a>`-to-pricing-page approach.
- [x] 2.4 The recommended-card ribbon on the landing MUST read `Más popular` (already aligned with task 5.1). Do not duplicate the `successful_sends_count` footer line — that line stays only on `/payments/paquetes/`.
- [x] 2.5 Verify the section renders correctly at 320, 768, 1024, and 1440 px (responsive grid `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3`, no horizontal overflow).

## 3. Spanish accent audit
- [x] 3.1 Run a defined-pattern audit using ripgrep against `templates/` (excluding `templates/admin/`). Results: only false positives from Tailwind CSS `via-` classes and English CSS comments.
- [x] 3.2 No real hits found — copy already correctly accented. Words like `automáticamente`, `inténtalo`, `suscripción`, `página`, `está`, `más`, `días`, `único` were confirmed present and accented.
- [x] 3.3 Manually re-read the four highest-traffic user-facing templates end-to-end: `templates/home.html`, `templates/base.html`, `templates/dashboard/index.html`, `templates/payments/packages.html`. No remaining unaccented Spanish words.
- [x] 3.4 Document: **No changes required — copy already correctly accented.**

## 4. Site max-width +20 %
- [x] 4.1 Replace `max-w-7xl` with `max-w-screen-2xl` in `templates/base.html` (lines 48, 100, 126, 147).
- [x] 4.2 Replace `max-w-7xl` with `max-w-screen-2xl` in `templates/home.html` (lines 12, 36, 83, 107).
- [x] 4.3 Replace `max-w-7xl` with `max-w-screen-2xl` in `templates/payments/packages.html:6`.
- [x] 4.4 Replace `max-w-7xl` with `max-w-screen-2xl` in `templates/dashboard/index.html:17`.
- [x] 4.5 Replace `max-w-7xl` with `max-w-screen-2xl` in `templates/mailing/unsubscribe.html:7`, `templates/mailing/unsubscribe_confirm.html:7`, `templates/mailing/cv_not_found.html:7`, `templates/mailing/cv_revoked.html:7`.
- [x] 4.6 Final grep `rg -n 'max-w-7xl' templates/` returns zero matches.
- [x] 4.7 Visually verify (or via Playwright headless screenshot) at 1440 and 1920 px that the navbar, hero, and footer feel wider — but at 320, 375, 768, 1024 px nothing changed and no horizontal overflow appears (the `Responsive design invariants` requirement is preserved).

## 5. Pricing ribbon label "Recomendado" → "Más popular"
- [x] 5.1 Edit `templates/payments/packages.html:18` — replace the string `Recomendado` with `Más popular`.
- [x] 5.2 Grep `rg -in 'Recomendado' templates/ apps/` — zero matches in user-facing templates.

## 6. Footer: Instagram with scalable social structure
- [x] 6.1 **Create `apps/core/context_processors.py`** — define `social_links(request)` returning `{"social_links": [...]}`. Register the processor in `config/settings.py:TEMPLATES[0]["OPTIONS"]["context_processors"]`. Run `python manage.py check` — confirmed no issues.
- [x] 6.2 Define the initial list with exactly one entry: Instagram, url `https://instagram.com/joinfastjob`, aria-label `FastJob en Instagram`, inline SVG glyph (Instagram's official trademark monoline mark, 24×24, `currentColor` fill).
- [x] 6.3 Add social links `<div>` in footer between copyright and legal-links cluster. Each link uses `text-gray-500 hover:text-brand transition`, `aria-label`, `target="_blank"`, `rel="noopener"`.
- [x] 6.4 Footer layout preserves existing invariants: at `< sm` stacked vertically; at `sm+` copyright left, socials middle, legal links right.

## 7. Header label change "Panel" → "Panel de envíos"
- [x] 7.1 Edit `templates/base.html:67` — change desktop "Panel" to "Panel de envíos" with `whitespace-nowrap`.
- [x] 7.2 Edit `templates/base.html:109` — change mobile-drawer "Panel" to "Panel de envíos".
- [x] 7.3 Edit `templates/base.html:62` — change email span from `hidden sm:block` to `hidden lg:block`.
- [x] 7.4 Verify at viewports 768, 1024, 1280, and 1440 px that the authenticated navbar renders on a single horizontal row without overflow.
- [x] 7.5 Verify at viewports 320 and 375 px that the hamburger drawer opens and the new "Panel de envíos" label fits without overflow.

## 8. Validation
- [x] 8.1 Run `openspec validate refresh-landing-shell-and-cv-attachment-copy --strict` — valid.
- [x] 8.2 Run the project test suite (`pytest -q`) — 321 passed, 3 pre-existing failures (unrelated to this change).
- [x] 8.3 Run `python manage.py check` — system check identified no issues (0 silenced).
