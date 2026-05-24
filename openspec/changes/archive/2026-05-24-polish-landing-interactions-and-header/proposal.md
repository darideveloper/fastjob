# Change: Polish landing interactions, sticky header, larger logo, and filter UX

## Why
The public landing experience at https://fastjob.es feels visually static and inherits a few small UX gaps that have surfaced as the site matures:

- Buttons and links (especially the two hero OAuth CTAs and inline navbar links) lack distinct, brand-matched hover affordances, so they read as flat at first glance.
- The header sits inline at the top of the document; on long pages (landing, packages, dashboard) the navbar scrolls out of view, forcing users back to the top to switch sections or log in.
- The current navbar logo (`h-11`) reads small against the surrounding type scale and is undersized for a brand-first landing.
- The filter widgets in the public company-finder use generic "Selecciona opciones…" placeholders, which fail to signal that the field is type-to-search — many users don't realise they can filter by typing.
- The filter dropdowns cap at `max-h-48` (≈ 4-5 options visible), making the existing whitelist feel smaller than it is and forcing extra scrolling.

All five items are scoped to the **final-user surface** (landing, packages, dashboard chrome, auth screens) — not Django admin.

## What Changes

- **Hover effects across buttons and links** — establish a consistent, brand-matched hover baseline in `ui-shell` (applied via existing brand tokens, no new CSS framework). Hero CTAs get explicit, brand-distinct visual styles: Google remains a clean white card with a brand-blue hover ring, while Microsoft uses a bold dark background (`bg-gray-900`) at rest. Both maintain shared "lift" and "scale" interactions.
- **Sticky global navbar with smooth elevation transition** — the navbar in `base.html` becomes `position: sticky` at the top of the viewport. While the page is at scrollY ≤ 8 px, the navbar renders in its current "flat" state (transparent shadow, full logo size). After the user scrolls past that threshold, the navbar smoothly (≤ 200 ms) elevates: shadow appears, height/padding shrinks slightly, logo scales down slightly to a "sticky-compact" size. The transition MUST honour `prefers-reduced-motion`.
- **Larger navbar logo (~30 %)** — the at-rest logo height grows from `h-11` (44 px) to `h-14` (56 px), a +27 % increase that visually reads as the requested "≈ 30 %". The sticky-compact state uses `h-11` (the previous size) so vertical real-estate while scrolling is unchanged. Aspect ratio (1226 : 450) is preserved; CLS budget unchanged.
- **More descriptive filter placeholders** — `data-placeholder="Todos los sectores…"` becomes `Escribe o elige un sector (ej. Tecnología)…`, and `Todas las ubicaciones…` becomes `Escribe o elige una ubicación (ej. Madrid)…`. The localized "Escribe o elige" half explicitly tells the visitor the field is type-to-search.
- **Filter dropdowns show at least 8 selectable options** — `max-h-48` (12 rem ≈ 192 px, ≈ 5 options) becomes `max-h-96` (24 rem ≈ 384 px, ≥ 9 rows at the current `py-2 text-sm` row height). This guarantees 8 selectable options even when the "— Limpiar todos —" helper row is present at the top of the dropdown (which happens whenever the visitor has at least one pill selected). The list still scrolls when the whitelist exceeds the visible capacity; only the visible capacity changes.
- **Brand-matched Social Login Buttons** — the social login screen (`login.html`) features differentiated hover states: Google uses a light-blue tint and blue border, while Microsoft uses a light-gray tint and cyan border. Both carry the site-wide "lift" effect.

## Impact

- **Affected specs:**
  - `ui-shell` — sticky header behavior added; logo size requirement modified; hover baseline added.
  - `landing` — filter placeholder copy added; dropdown visible-capacity added; hero CTA hover state reinforced.
- **Affected code:**
  - `templates/base.html` — navbar markup + sticky `<script>` snippet + Tailwind config additions for the transition.
  - `static/js/combobox.js` — `max-h-48` → `max-h-80` on the dropdown `<ul>` className list.
  - `templates/home.html` — `data-placeholder` attribute values on the two filter combobox containers; hover-class additions to hero CTAs and the company-finder CTA.
- **No new third-party dependencies.** The sticky behavior is a ~20-line vanilla JS scroll listener using `requestAnimationFrame` throttling (consistent with the existing first-party-only posture documented in `ui-shell`).
- **No Django admin changes.** No new server routes, no template-tag changes, no database migrations.
- **Localization:** Spanish copy only (matches `LANGUAGE_CODE = "es"`).
- **Accessibility:** preserves WCAG AA contrast already enforced by `ui-shell`; sticky navbar respects `prefers-reduced-motion`; hover states must not be the sole visual signal (focus states already covered by the existing focus-ring requirement).
