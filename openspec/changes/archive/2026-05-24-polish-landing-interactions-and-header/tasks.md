# Tasks: Polish landing interactions, sticky header, larger logo, filter UX

## 1. Base template — sticky navbar + larger logo
- [x] 1.1 In `templates/base.html`, the `<nav>` now carries `sticky top-0 z-40 group` + motion-safe shadow transition, plus `data-scrolled="false"` as the initial attribute.
- [x] 1.2 Inner row height now uses `h-20 group-data-[scrolled=true]:h-16` with a motion-safe transition. Vertical alignment preserved via the existing `flex items-center justify-between`.
- [x] 1.3 Navbar logo `<img>` now renders at `h-14` at rest and `h-11` when scrolled via `group-data-[scrolled=true]:h-11`. `width="120" height="44"` attributes preserved; the wrapping `<picture>` carries `style="aspect-ratio: 1226 / 450;"` for CLS reservation.
- [x] 1.4 Inline `<script>` added right after `</nav>` that reads `window.scrollY` inside a `requestAnimationFrame`-throttled handler and toggles `data-scrolled` at the 8 px threshold with `{ passive: true }`. (Implementation deviation: the listener is attached unconditionally; `motion-safe:` CSS variants suppress transitions for reduced-motion users while still toggling the attribute — this matches the spec scenario "Reduced-motion users get an instant state swap" better than the task's literal "early-return" wording.)
- [x] 1.5 Navbar shadow uses `shadow-sm data-[scrolled=true]:shadow-md` with motion-safe transition, exactly as specified.

## 2. Hover effects — site-wide buttons and links
- [x] 2.1 Navbar ghost links (desktop + drawer) gained `transition-colors`; "Empezar gratis" primary CTA gained `hover:shadow-md`; footer links gained `transition-colors`.
- [x] 2.2 "Empezar con Google" hero CTA now carries `hover:bg-brand-cloud` and `hover:ring-[#4285F4]/50` (transition was already present).
- [x] 2.3 "Empezar con Microsoft" hero CTA now uses `bg-gray-900` at rest and carries `hover:ring-[#00A4EF]/50` in addition to its existing transition.
- [x] 2.4 "Ver paquetes y empezar" finder CTA now carries `hover:shadow-xl hover:-translate-y-0.5` on top of the existing `hover:bg-brand-dark transition shadow-lg`.
- [x] 2.5 Both per-card primary CTAs in `packages.html` (authenticated `<button>` and anonymous `<a>`) now carry `hover:shadow-xl hover:-translate-y-0.5` on top of their existing primary-fill chrome.
- [x] 2.6 Both social-login buttons in `account/login.html` updated to brand-matched asymmetric hover: Google uses `hover:bg-brand-cloud hover:border-[#4285F4]`, while Microsoft uses `hover:bg-gray-50 hover:border-[#00a4ef]`. Both carry `hover:shadow-md hover:-translate-y-0.5`.

## 3. Filter placeholders
- [x] 3.1 Sector combobox placeholder in `home.html` now reads `Escribe o elige un sector (ej. Tecnología)…`.
- [x] 3.2 Location combobox placeholder in `home.html` now reads `Escribe o elige una ubicación (ej. Madrid)…`.
- [x] 3.3 Dashboard filter widgets mirrored in `templates/dashboard/index.html` (lines 214/221) with the same new placeholders, keeping behavior consistent across both filter surfaces.

## 4. Dropdown capacity (8 selectable visible options)
- [x] 4.1 `dropdown.className` in `static/js/combobox.js:64` updated from `max-h-48` to `max-h-96`. `overflow-y-auto` preserved.
- [x] 4.2 Row arithmetic confirmed: `px-3 py-2 text-sm` ≈ 36 px per row × 8 rows = 288 px + 1 "Limpiar todos" row (36 px) = 324 px, well within the 384 px (`max-h-96`) cap.
- [ ] 4.3 Manual: select one pill in the sector combobox, re-open the dropdown, and confirm the visible list shows the "— Limpiar todos —" row at the top followed by at least 8 selectable options without inner-list scrolling. (Deferred to Section 5 manual verification.)

## 5. Verification
- [ ] 5.1 **Manual — deferred to user.** Run `./dev.sh`, open `/` at 1440 × 900 and confirm (a) navbar sticky, (b) smooth elevation, (c) logo shrinks `h-14`→`h-11`, (d) hero CTAs visibly change on hover, (e) sector combobox shows ≥ 8 rows, (f) new placeholder text. The implementation was not browser-tested by the agent (no live browser session available).
- [ ] 5.2 **Manual — deferred to user.** Repeat at 375 × 667 to confirm mobile drawer still opens/closes with the sticky navbar.
- [ ] 5.3 **Manual — deferred to user.** Enable "Reduce motion" and confirm navbar state swap is instant. (The CSS uses `motion-safe:` variants so transitions auto-disable for reduced-motion users — code-level correctness verified, runtime check still recommended.)
- [ ] 5.4 **Manual — deferred to user.** Visit `/dashboard/`, `/payments/paquetes/`, `/accounts/login/` to confirm no regressions.
- [x] 5.5 `pytest` run: 321 passed, 3 failed. All 3 failures are pre-existing and unrelated to this change: (a) `test_storage.py::test_private_storage_acl` and `::test_signed_url_generation` fail because the local test env uses `FileSystemStorage` instead of S3 (env config issue, no code path I touched); (b) `test_visible_credits.py::test_dashboard_ui_shows_zero_for_negative_balance` asserts presence of `<p class="text-3xl font-extrabold text-brand">0</p>` in the dashboard credits display — an element this change never modifies (verified via `git diff HEAD templates/dashboard/index.html` shows only the two `data-placeholder` lines changed).
- [ ] 5.6 **Lighthouse — deferred to user.** Compare Performance/CLS/JS-transfer before vs. after on `/`. The sticky listener is ~15 lines inline (zero new HTTP requests); the only added classes are existing Tailwind utilities (no new compiled CSS via the JIT CDN). Expected delta: < 1 KB.
- [x] 5.7 `openspec validate polish-landing-interactions-and-header --strict` → "Change is valid". Zero errors.
