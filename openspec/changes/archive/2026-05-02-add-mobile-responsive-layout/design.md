# Design notes — add-mobile-responsive-layout

## Context

This change spans three concerns that interact:

1. The **global navbar** in `templates/base.html` is shared by every
   server-rendered page (audited: home, dashboard, packages, success,
   login, cv_not_found, unsubscribe, delete_account). Any structural
   change is felt everywhere.
2. The **dashboard activity table** is the densest data view in the app
   and the only view with a real `<table>`; how we make it responsive
   sets a precedent for any future tabular view (campaign history,
   billing history, blacklist).
3. The **login page** crashes today because of the C3 OAuth-only
   hardening. We must not regress that hardening (no signup form, no
   password endpoints) while restoring the page.

Because two of these need shared judgement (where to put breakpoints,
how to keep the C3 posture intact), we capture the trade-offs here
rather than litigating them inside spec deltas.

## Decision 1 — Hamburger menu approach

**Three options considered:**

| Option | Effort | Pros | Cons |
| --- | --- | --- | --- |
| A. Inline vanilla JS toggle (~10 lines) | S | No new dep; works without JS framework; cache-friendly | Slightly verbose duplicate of a pattern Alpine solves in 1 attribute |
| B. Adopt Alpine.js via CDN | M | One-liner per toggle; idiomatic for "small islands of interactivity" | New CDN script (~7 KB gzipped); learning surface for the team |
| C. Pure-CSS via `:checked` hack on a hidden checkbox | S | Zero JS | Accessibility footguns (focus management, esc-to-close); doesn't read as a button to assistive tech |

**Decision: A (inline vanilla JS).** The toggle is a single button + a
`hidden`-class flip. The C3 review explicitly minimized the trusted
surface area; adding Alpine via CDN means one more origin to vet. The
`:checked` hack would also force us to re-do focus management to keep
the hamburger keyboard-accessible. ~10 lines of `addEventListener` is
the cheapest correct answer.

**Open question:** keep the toggle inline in `base.html`, or extract to
`static/js/navbar.js` (mirroring `static/js/combobox.js`)? Slight
preference for inline because (a) it must run before paint to avoid
the menu flashing open and (b) every other page already loads the same
`base.html`, so there is no DRY win from extracting.

## Decision 2 — Breakpoint for the navbar collapse

**Options:** collapse below `sm` (640 px) vs. below `md` (768 px).

**Decision: `md` (768 px).** Measured at 768 px, the authenticated
navbar still fits without overflow — but it is *visually* tight: the
credits chip + "Panel" + "Comprar" + "Salir" + email leaves ~30 px of
slack. At 720 px (the iPad-portrait split-view width), it would
overflow. Collapsing below `md` gives breathing room on tablets in
split-view, and the desktop look (≥ 768 px) is identical to today.

The audit's anonymous-user finding (logo + "Iniciar sesión" + "Empezar
gratis" colliding at 320–375 px) is also fixed at the `md` threshold
without a separate carve-out.

## Decision 3 — Activity table: min-width vs. card stack

**Options:**

| Option | Effort | Pros | Cons |
| --- | --- | --- | --- |
| A. `min-w-[640px]` on `<table>` (lets the existing `overflow-x-auto` wrapper actually engage) | S | One-line fix; preserves table semantics for screen readers; matches Tailwind community pattern | Requires horizontal scroll on small phones |
| B. Card-stack: `<div>` per row below `sm`, `<table>` above `sm` | L | Prettier on phones; no horizontal scroll | Duplicate markup OR fragile CSS contortions; loses table semantics; templating overhead |

**Decision: A.** The audit explicitly noted `overflow-x-auto` is wired
on the wrapper but never triggered because `<table class="w-full">`
collapses to fit. The one-class fix unblocks the existing markup,
preserves `<table>` semantics for assistive tech, and matches a
well-known Tailwind pattern (`overflow-x-auto` + `min-w-[…]`). If user
research later shows phone users are scrolling tables awkwardly, B
remains a future-compatible upgrade path.

## Decision 4 — Login bug fix: stub URL vs. subclass `LoginView`

**Options:**

| Option | Effort | Pros | Cons |
| --- | --- | --- | --- |
| A. Add `path("accounts/signup/", RedirectView.as_view(pattern_name="account_login", permanent=False), name="account_signup")` | XS | One line; no logic; survives allauth upgrades | Adds one public URL (defensible: redirects to OAuth login) |
| B. Subclass `LoginView` and override `get_context_data` to omit `signup_url` | S | No new public URL | Drift risk if allauth changes the context shape (the C3 comment exists *because* allauth's URL surface evolves); fragile coupling to a private internal contract |
| C. Catch the `NoReverseMatch` in a custom `urlconf` setting | M | No new URL, no subclass | Hides the underlying problem; harder for the next reader to diagnose |

**Decision: A.** It is the smallest possible change that survives
arbitrary allauth upgrades, and the redirected-to URL (`account_login`)
is exactly where a user fumbling at `/accounts/signup/` should end up
in an OAuth-only product. No security regression: there is no
`signup_view` mounted, just a `RedirectView`. We document the rationale
in a comment alongside the existing C3 block in `config/urls.py`.

## Decision 5 — File input styling

The `<input type="file">` shows browser-default labels ("Choose File" /
"No file chosen") in English on Chrome, regardless of `lang="es"`. This
is browser-controlled UA shadow DOM — Tailwind's `file:` pseudo-class
modifiers (`file:bg-indigo-50`, etc.) only style the **button**, not
the **filename label** next to it.

**Decision:** wrap the input in a styled `<label>` and hide the input
with `class="sr-only"`. The label gets the existing brand button
classes; a small inline JS listener (`change` event) updates a sibling
`<span>` with the chosen filename in Spanish ("Sin archivo
seleccionado" / actual filename). This is the canonical pattern and
matches the rest of the design system. No new dependency.

## What this change explicitly does NOT do

- **No Tailwind build pipeline migration.** The audit-level fixes can
  be expressed entirely with arbitrary-value Tailwind utilities (e.g.
  `min-w-[640px]`) which the CDN already supports.
- **No design refresh.** Every desktop layout is byte-identical
  (modulo Tailwind class strings).
- **No reusable component extraction.** The hamburger lives once in
  `base.html`; the file-input pattern lives once in
  `dashboard/index.html`. Premature abstraction is explicitly skipped
  per the project's "no half-finished implementations" guidance.
- **No allauth signup flow.** The `account_signup` URL is a stub
  redirect, not a form. The C3 hardening posture is preserved verbatim.

## Risks

1. **Hamburger toggle JS regressions.** Mitigation: include a Playwright
   smoke test that asserts the menu opens on click at 320 px and closes
   on outside click + Esc.
2. **Status badge clipping fix relies on the navbar fix.** The audit
   noted that badges (`Enviado` / `Fallido`) clip to `Enviad…` /
   `Fallid…` only because the body is overflowing. If we ship the table
   fix without the navbar fix, the table looks correct but the page
   itself is still broken; if we ship the navbar fix without the table
   fix, the table cells wrap to 6 lines. They are co-dependent — ship
   together.
3. **Alpine-considered-and-rejected might come back.** If a future
   change wants Alpine for a more complex widget (e.g. multi-step
   checkout), the inline JS pattern from this change is a 5-minute
   port. We are not painting ourselves into a corner.
