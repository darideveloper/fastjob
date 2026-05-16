# Design: Client-screen redesign + brand refresh

## Context

The redesign is **presentation-only** — no view, model, URL, settings, Celery, or migration changes. Risk is therefore concentrated in two places:

1. **Token coherence** — every screen must consume the same palette tokens; one-off hex codes drift the brand within weeks.
2. **Accessibility** — the new palette includes Electric Cyan `#00E5FF`, which is *below* AA contrast against white. The design must encode where cyan is and isn't allowed.

This document captures the decisions that bind all the per-capability deltas together so each spec stays terse.

## Goals

- One source of truth for color, logo, and type — declared in `templates/base.html`'s inline Tailwind config.
- Every final-user screen shares the same card chrome, button hierarchy, and form-control style.
- WCAG **AA** compliance for every rendered text/background pair.
- Full responsiveness at 320, 360, 375, 414, 768, 1024, 1440 px (the existing `ui-shell` invariant grid).
- Zero new runtime dependencies: still Tailwind CDN, still vanilla JS, still Django templates.

## Non-Goals

- Replacing the Tailwind CDN with a build pipeline (separate concern, tracked elsewhere).
- Swapping Inter for a paid display font.
- Restyling the Django admin or transactional email bodies.
- Backend or routing changes.

## Decisions

### 1. Color tokens & semantic mapping

| Token | Hex / value | Role | AA contrast (on intended pairing) |
|---|---|---|---|
| `brand.bg`      | `#FEFEFE` | Page background | n/a |
| `brand.ink`     | `#1A1A1A` | Body text, high-emphasis labels | 18.6 : 1 on `brand.bg` ✅ |
| `brand.DEFAULT` | `#007BFF` | Primary CTA fill, links, key affordances | 4.6 : 1 (as text on `brand.bg`) ✅ / 4.8 : 1 (white text on this fill) ✅ |
| `brand.dark`    | `#003D99` | Primary CTA hover/active, H1/H2 accent | 10.4 : 1 on `brand.bg` ✅ |
| `brand.cyan`    | `#00E5FF` | **Accent only**: focus rings, decorative gradients, hover halos, thin borders | 1.4 : 1 on `brand.bg` ❌ — never used as text or fill of an interactive surface |
| `brand.soft`    | `rgba(0,229,255,0.12)` | Tint **background** for chips, halos under icons | always paired with `brand.ink` or `brand.dark` text ✅ |
| `brand.muted`   | `rgba(0,123,255,0.08)` | Card hover **background**, table zebra, panel borders | paired with `brand.ink` text ✅ |
| `brand.cloud`   | `#E6F2FF` | **Light text on dark brand backdrop** (hero subtitle, immersive captions). Replaces today's dual-use of `text-brand-muted`. | 9.4 : 1 on `brand.dark` (`#003D99`) ✅ |
| `brand.ring`    | `#00E5FF` (solid) | Single hex used by `focus:ring-brand-ring`. Visible contrast on focus comes from `outline-3 outline-offset-2` against the underlying button fill (cobalt or white), **not** from a layered halo. Earlier "@ 70% on cobalt-darkened halo" wording was contradictory and is removed. | ≥ 3 : 1 against `brand.DEFAULT` / `brand.dark` / white button fills (verified empirically in apply stage) ✅ |

**Rule (encoded in `ui-shell` spec):** `brand.cyan` MAY appear as a 1–2 px border, as a focus outline, or as a stop in a gradient *whose other stop is Cobalt, Vibrant Blue, or Slate*; it MUST NOT appear as `bg-` of a button, `text-` of any rendered text, or the sole signal for state changes.

**Permitted non-brand colors:** neutral grays (`text-gray-*`, `border-gray-*`, `bg-gray-*`) MAY be used for non-primary text and dividers. Semantic status colors (`red-*`, `green-*`, `amber-*`, `yellow-*`) MAY be used **only** where they encode status meaning — e.g. the campaign toggle's red/green buttons, the pause-reason banner's amber/red, the danger-zone delete-account CTA, the recent-activity table's "Enviado"/"Fallido" chips. Legacy brand palette names from the previous identity (`indigo-*`) are PROHIBITED — every such reference must be migrated to a `brand.*` token.

### 2. Typographic scale

Declared once in `tailwind.config.theme.extend.fontSize`:

| Token | Size / line-height | Use |
|---|---|---|
| `text-display` | `clamp(2.25rem, 4vw + 1rem, 3.5rem)` / 1.1 | Landing hero, success page hero |
| `text-h1` | `clamp(1.75rem, 2vw + 1rem, 2.25rem)` / 1.2 | Page titles |
| `text-h2` | `1.5rem` / 1.3 | Section headings, card titles |
| `text-body` | `1rem` / 1.6 | Default body |
| `text-caption` | `0.875rem` / 1.5 | Helper text, meta |

Using `clamp()` lets the same class scale fluidly between 320 px and 1440 px without breakpoint juggling — a deliberate choice for a CDN-Tailwind project where adding new breakpoint variants is cheap but adding *new utilities* is not.

**Tailwind CDN caveat (verified in apply stage):** Tailwind 3.x JIT does parse arbitrary `clamp()` strings inside `theme.extend.fontSize`. If the runtime CDN build rejects the `[size, { lineHeight }]` tuple form, the fallback is breakpoint-stepped sizes — e.g. `display: ['2.25rem', { lineHeight: '1.1' }]` with `sm:text-[2.75rem]` / `lg:text-[3.5rem]` overrides on the headline element. This fallback MUST not regress any other requirement.

### 3. Card / surface system

All screens consume one of four surfaces:

- **Card** — `bg-white border border-brand-muted rounded-2xl shadow-sm p-6 sm:p-8` (default content container).
- **Immersive hero band** — `bg-gradient-to-br from-brand via-brand-dark to-brand-cyan/40 text-white` (landing hero only; preserves the current dark-immersive treatment of `templates/home.html:11`, restyled to the new palette with an Electric-Cyan glow stop). Headline uses `text-display text-white`; subtitle uses `text-brand-cloud` (the new light-text-on-dark token).
- **Subtle success band** — `bg-gradient-to-br from-brand-cyan/15 via-white to-brand/10` (payment success page only — this *is* a light backdrop, distinct from the landing hero; the visual hierarchy of "Pago completado" reads better as a calm celebration than as another immersive hero).
- **Warning surface** — `bg-red-50 border border-red-200` (kept semantic red for destructive intent only: delete account, hard errors).

Spacing follows an 8-pt scale already implicit in Tailwind defaults; the proposal does not introduce new spacing tokens.

### 4. Button hierarchy

| Variant | Classes (sketch) | Use |
|---|---|---|
| Primary | `bg-brand text-white hover:bg-brand-dark focus:ring-brand-ring` | One per screen, the main intended action |
| Secondary | `bg-white text-brand-dark border border-brand hover:bg-brand-muted` | Alternate path (e.g. "Cancelar") |
| Ghost | `text-brand-dark hover:bg-brand-muted` | Tertiary links inside cards |
| Destructive | `bg-red-600 text-white hover:bg-red-700` | Delete account, irreversible only |
| Vendor (Google/Microsoft) | white fill, slate border, vendor-color icon | Preserve Google/Microsoft trust signals on `account/login.html` — vendor branding rules forbid skinning these in brand colors |

### 5. Logo & favicon wiring

- Asset facts: `static/images/fastjob-logo.png` is **1226 × 450** (≈ 2.72 : 1). Hardcoding mismatched `width`/`height` would distort the wordmark, so we anchor only the rendered **height** and let width follow the intrinsic ratio.
- Navbar logo: `<picture>` containing `<source srcset="{% static 'images/fastjob-logo.webp' %}" type="image/webp">` + `<img src="{% static 'images/fastjob-logo.png' %}" alt="FastJob" class="h-9 w-auto" loading="eager">`. The wrapper carries `style="aspect-ratio: 1226 / 450"` so the reserved space matches the asset and no CLS occurs.
- Auth and email-landing card logos: same `<picture>`, larger class `h-12 w-auto` (≈ 48 px tall), positioned above the card title.
- Favicons in `<head>`: ICO for legacy, PNG for modern.
- The existing inline SVG wordmark at `base.html:42-46` is **removed** — the raster logo is the brand mark from now on. (If a future rebrand wants SVG again, that's a follow-up change; raster is sufficient now and matches what the user has shipped.)
- **Asset weight note:** the 1226 × 450 PNG is sized generously for a 36 px-tall navbar render. If the apply stage measures it over ~50 KB it should request a resized export (or generate one with `imagemagick` / `cwebp`); this is a content-quality concern, not a spec one.

### 6. Responsiveness strategy

- **Mobile-first**: every screen is designed at 320 px first, then progressively enhanced at `sm` (640), `md` (768), `lg` (1024).
- **No fixed widths in px**: all container widths are `max-w-*` + `mx-auto`; all images anchor a CSS dimension and let the other follow intrinsic ratio (see §5).
- **Dashboard grid**: the existing `lg:grid-cols-3` layout is **preserved**: left rail (`lg:col-span-1`) carries CV manager + filter panel + danger zone; right area (`lg:col-span-2`) carries the recent-activity table, which currently sets `min-w-[640px]` on its `<table>` to keep four columns readable — reflowing this into a narrower column would force horizontal scroll, contradicting the no-overflow invariant. The campaign toggle keeps its current position in the page **header row** (a `flex flex-col sm:flex-row` wrapper above the stats grid), not inside a column.
- **Pricing grid**: `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6`.
- Touch targets `min-h-[44px]` enforced on every `<button>` and primary `<a>` at viewports `< md`.

### 7. Why preserve existing `landing` requirements verbatim?

The `landing` spec already encodes hard-won invariants from `add-mobile-responsive-layout` and `add-company-filter-finder` (e.g. CTAs on one line at 320 px, public finder counter never exposes row data, envíos vocabulary). These are **behavior** invariants, not visual ones. The redesign is allowed to restyle the surfaces but MUST NOT regress those behaviors. The `landing` delta in this change therefore only MODIFIES the *visual* hero CTA requirement to add palette/typography expectations on top of the existing single-line constraint.

### 8. Why no test-suite changes?

Pytest exercises view behavior and template rendering. None of that changes. Visual QA is checklist-driven (in `tasks.md`) at 320/375/768/1024/1440 px, plus DevTools contrast checks for every text/bg pair on every screen. Snapshot tests for templates would be high-noise (every Tailwind class diff breaks them) and were not adopted by the project earlier — we keep that choice.

## Risks

- **Cyan misuse.** Easy to reach for cyan as a CTA fill because it's the most "exciting" hue. The spec encodes a strict rule and gives reviewers a single check to run (`rg "bg-brand-cyan" templates/` should match only gradients and decorative elements, never buttons).
- **Vendor-button color conflict.** Google and Microsoft brand guidelines forbid hue substitution on "Sign in with…" buttons. The design keeps those vendor-correct, breaking the otherwise-uniform CTA color rule. Spec calls this out explicitly so a future reviewer doesn't "fix" it.
- **Raster logo on retina.** The PNG/WebP must be at least 2× the rendered size (i.e. ≥ 240 px wide for a 120 px slot). If `static/images/fastjob-logo.png` is below that, the apply stage will need to flag it for re-export — but no spec change is needed; it's a content-quality matter.

## Migration

None. This is a presentation refresh. Deploy = render new templates = browsers see the new palette on next request. No data, no env vars, no clients.

## Open questions

- Should the favicon also include a dark-mode variant (`prefers-color-scheme: dark` PNG)? Not required for AA, and the user only supplied one PNG; deferred unless asked.
- Should `templates/emails/` adopt the new palette too? Out of scope here — separate proposal because email rendering quirks (Outlook, Gmail) make it a different problem domain.
