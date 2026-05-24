# Change: Refresh landing shell and align copy with CV-attachment flow

## Why
Several user-visible strings and structural details on the public site still reflect the previous link-based CV delivery flow, even though `apps/mailing/migrations/0008_auto_20260514_0522.py` already switched email sending to PDF attachments. In parallel, the landing page is missing a pricing surface that converts visitors, the global container feels narrow on large monitors, the pricing "Recomendado" tag is weaker than the industry-standard "Más popular", the footer has no social presence, and the authenticated navbar label "Panel" is ambiguous. This change groups the related polish, copy, and structural fixes into a single proposal so the landing experience and shell come back into a consistent state.

## What Changes

### 1. Remove "enlace(s) de descarga" terminology end-to-end
- Reword `templates/home.html` line 18 (hero subtitle) and lines 88–89 (trust-signal card) so neither references "enlaces de descarga" nor "Sin adjuntos" — the product now sends attachments, so both strings are factually wrong.
- Reword `templates/mailing/cv_not_found.html` line 31 and `templates/mailing/cv_revoked.html` lines 3 + 25–26 so the wording no longer mentions "enlace de descarga" / "descarga revocada" — the templates remain reachable for legacy links from the pre-attachment era, but their copy must be neutral ("Este enlace ya no está disponible", etc.).
- Do **not** edit the historical migrations (`0002_seed_templates.py`, `0008_auto_20260514_0522.py`) — they are frozen by Django's migration contract and `EmailTemplate` rows in production were already updated by migration 0008.
- The `cv_download` view, URL (`apps/mailing/urls.py:5`), and `cv_download_token` field stay in place (per clarifying-question decision: "reword only") so historical email links keep resolving to the reworded error pages.

### 2. Add pricing cards section at the bottom of the home page
- Append a new "Paquetes" section to `templates/home.html` rendered immediately above `{% endblock %}` and below the company-finder section.
- Reuse the same `CreditPackage.objects.filter(is_active=True).order_by("price_eur")` query and the `successful_sends_count` aggregate that `apps/payments/views.py:packages()` already computes — extract a small helper or pass the data via the home view (`apps/core/views.py` or wherever `home.html` is rendered) so the markup stays declarative.
- Card markup is extracted into a shared partial `templates/payments/_package_card.html` used by both the landing page and the canonical pricing page — `{% include %}` with `package` and `is_popular` per card.
- Landing pricing CTAs use the **same auth-gated behavior** as `/payments/paquetes/`: anonymous users get a login-redirect link (`/accounts/login/?next=/payments/paquetes/`), authenticated users POST to Stripe checkout. This replaced the previous always-link-to-pricing-page approach so the landing cards behave identically to the canonical page.
- Card chrome must match `templates/payments/packages.html` (per the `Tiered pricing card visual hierarchy` requirement in `pricing/spec.md`) — now enforced by the shared partial.

### 3. Spanish accent audit and fixes
- Audit every server-rendered template under `templates/` for unaccented Spanish words. The current state is largely correct (the existing copy uses `envíos`, `sesión`, `conexión`, `automáticamente`, etc.), but we will run a defined-pattern audit during apply and document the result.
- Specifically validate the following surfaces that render to end users: `home.html`, `base.html`, `dashboard/index.html`, `dashboard/delete_account.html`, `payments/packages.html`, `payments/success.html`, `account/login.html`, `account/logout.html`, `socialaccount/*.html`, `mailing/*.html`, `404.html`, `500.html`.
- Out of scope: admin-only templates under `templates/admin/`, email-body strings inside historical migrations.

### 4. Increase site max-width by ~+20%
- Replace every `max-w-7xl` (1280 px) usage in user-facing templates with `max-w-screen-2xl` (1536 px) — exactly +20 %, no Tailwind config change required (per clarifying-question decision).
- Affected lines: `templates/base.html:48,100,126,147`, `templates/home.html:12,36,83,107`, `templates/payments/packages.html:6` (NB: this file currently uses `max-w-7xl` without `lg:px-8` — preserve its existing padding), `templates/mailing/unsubscribe.html:7`, `templates/mailing/unsubscribe_confirm.html:7`, `templates/mailing/cv_not_found.html:7`, `templates/mailing/cv_revoked.html:7`, `templates/dashboard/index.html:17`.
- Verify no horizontal-overflow regression at 320/375/768/1024/1440/1920 px (existing `Responsive design invariants for final-user screens` requirement in `ui-shell/spec.md` continues to apply).

### 5. Replace "Recomendado" with "Más popular" on the pricing card ribbon
- Update `templates/payments/packages.html:18` from `Recomendado` to `Más popular`.
- Update the `landing` and `pricing` spec deltas accordingly so the requirement text and scenarios reflect the new label (this is a **BREAKING** change to the `Tiered pricing card visual hierarchy` requirement in `pricing/spec.md`, which today pins the literal label `Recomendado`).

### 6. Add Instagram link in footer with a scalable structure
- Add a `SOCIAL_LINKS` context-processor (or a small template constant block at the top of `templates/base.html`) listing socials as `{name, url, svg_path}`. The footer SHALL iterate this list with `{% for social in social_links %}` so adding TikTok / LinkedIn later is one line, not a copy-paste.
- The initial list contains exactly one entry: Instagram pointing to `https://instagram.com/joinfastjob` (dummy handle per clarifying-question decision).
- Each social MUST render as an `<a>` with `aria-label`, a 24×24 inline SVG glyph, and the same hover treatment (`hover:text-brand`) as the existing footer links.
- The new social cluster must not break the footer's `flex flex-col sm:flex-row items-center justify-between` layout on mobile.

### 7. Header: rename authenticated "Panel" → "Panel de envíos" with responsive safety
- Update both occurrences of `Panel` in `templates/base.html` (line 67 desktop, line 109 mobile drawer) to `Panel de envíos`.
- **NOT in scope of this section:** the dashboard's own page heading `<h1>Panel de Control</h1>` (`templates/dashboard/index.html:63`) and the dashboard `<title>Panel de Control — FastJob</title>` (line 3 of that template) MUST remain unchanged. Only the **navbar link label** is renamed; the page that the link points to keeps its own identity copy.
- On the desktop cluster (`md+`), the longer label may push neighbors out of alignment when combined with the envíos chip and the user email. We will:
  - Add `whitespace-nowrap` to the `Panel de envíos` `<a>` so it never wraps,
  - Hide `{{ user.email }}` one breakpoint earlier (change `hidden sm:block` → `hidden lg:block`) so the row stays single-line at `md` (768 px) where the chip + new label already crowd the right cluster,
  - Verify `document.documentElement.scrollWidth === window.innerWidth` at 768, 1024, and 1440 px.
- On the mobile drawer (`< md`), the longer label has no layout impact (vertical stack) — only the string changes.

## Impact

- **Affected specs:**
  - `landing` — MODIFIED (`Landing page uses "envíos" terminology` adds a no-"enlace de descarga" clause; new requirement for the pricing-cards section; max-width invariant). ADDED Requirements for the bottom pricing cards.
  - `ui-shell` — MODIFIED (`Mobile-collapsing global navbar` scenario for the "Panel" → "Panel de envíos" relabel; max-width target tightened from `max-w-7xl` to `max-w-screen-2xl`; ADDED requirement for the scalable social-links footer).
  - `pricing` — MODIFIED (`Tiered pricing card visual hierarchy` ribbon label changes from `Recomendado` to `Más popular`).
  - `mailing` — MODIFIED (the two CV-link error pages stop using "enlace de descarga" / "Descarga revocada" wording; the `cv_download` view's contract remains, only the rendered copy changes).

- **Affected code:**
  - Templates: `templates/base.html`, `templates/home.html`, `templates/payments/packages.html`, `templates/payments/_package_card.html` (new shared partial), `templates/mailing/cv_not_found.html`, `templates/mailing/cv_revoked.html`, `templates/mailing/unsubscribe.html`, `templates/mailing/unsubscribe_confirm.html`, `templates/dashboard/index.html`, plus the audit pass over the remaining user-facing templates.
  - Views: `apps/core/views.py` (new) — `HomeView(TemplateView)` injecting `packages` and `successful_sends_count` into the home context. `config/urls.py` updated to route `""` to `HomeView` instead of `TemplateView.as_view(...)`.
  - Context processors: `apps/core/context_processors.py` (new) providing `social_links` with the Instagram entry; registered in `config/settings.py`.

- **Out of scope:**
  - Renaming or removing `cv_download`, `cv_download_token`, the `/cv/<token>/` URL, or the `MailingLog.cv_download_token` field.
  - Editing historical migrations (`0002_seed_templates.py`, `0008_auto_20260514_0522.py`).
  - Admin templates under `templates/admin/` (Django admin pages do not extend `templates/base.html`, so the new social footer and the new max-width cap intentionally do not apply there).
  - Adding real Instagram, TikTok, or LinkedIn accounts — the URL is a dummy.
  - Any change to the Stripe checkout flow or the pricing model itself.
  - Pruning the now-dead `{cv_url}` mention in `EmailTemplate.body_html.help_text` (originating from `apps/mailing/migrations/0004_alter_emailtemplate_body_html.py`) — this is an admin-only help string and is left for a separate, narrowly scoped cleanup.

## Ordering / Conflicts with pending peer changes

Two other proposals are pending in `openspec/changes/` and touch overlapping files. To avoid merge conflicts and behavioural drift, apply this change **after** both peers (or coordinate explicitly):

1. **`openspec/changes/polish-landing-interactions-and-header/`** modifies `templates/base.html` extensively: sticky navbar behavior, logo size `h-11` → `h-14` at-rest with a sticky-compact state, and hero CTA hover treatment. This change's task 7 (the `Panel` → `Panel de envíos` relabel + `whitespace-nowrap` + email-span breakpoint shift to `lg+`) edits the **same navbar markup**. Re-base task 7 on top of the polished navbar so the `whitespace-nowrap` and `hidden lg:block` edits land on the correct (possibly renumbered) lines.

2. **`openspec/changes/update-pricing-cards-copy-and-fake-sends/`** modifies `templates/payments/packages.html` (the per-card feature label `CVs enviados` → `CVs enviados exitosamente`, already visible in the working tree at line 42) and changes `apps/payments/views.py:packages()` to compute `successful_sends_count = max(real_count, SystemSettings.get().displayed_sends_floor)`. This change's task 5.1 (ribbon line 18 `Recomendado` → `Más popular`) touches the **same file**; task 2.1 (home-view context) MUST reuse the **same `displayed_sends_floor`-aware computation** so the landing teaser and the canonical pricing page never display divergent numbers. If the peer is not yet shipped at apply time, task 2.1 falls back to the simpler `MailingLog.objects.filter(status="sent").count()`.
