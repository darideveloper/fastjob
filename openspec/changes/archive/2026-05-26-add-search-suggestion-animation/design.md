## Context

The public landing page and authenticated dashboard both present a company-finder filter section with two combobox widgets (Sector/Area and Location) and a live company count. Current usability research (and the spec history for "Filter widget placeholders signal type-to-search") indicates that visitors benefit from explicit cues that the filters support free-text search. A typewriter-animated suggestion line — cycling through real area+location combinations — would make this affordance immediately visible.

The project has no npm build pipeline; all frontend JS is vanilla, vendored, and loaded via `<script>` tags in `templates/base.html`. The existing animation system (`data-reveal` + `reveal.css`) is CSS-only with an IntersectionObserver. Typed.js (~7 KB minified) is the chosen animation library, vendored into `static/js/vendor/`.

## Goals / Non-Goals

- **Goals:**
  - Show a typewriter-animated suggestion under each filter-section heading, built from live Area+Location data
  - Make the suggestion clickable to pre-fill the comboboxes (fill-only on dashboard; navigate to results on landing)
  - Pause animation while a combobox is focused to reduce distraction
  - Respect `prefers-reduced-motion` with a static fallback
  - Keep the feature zero-impact on existing combobox behaviour (count updates, error handling, retry)

- **Non-Goals:**
  - Adding an autocomplete/suggestion dropdown below the combobox input (the combobox already has its own dropdown)
  - Adding server-rendered suggestion data (the feature will reuse the client-fetched filter options)
  - Adding a full-text search bar separate from the comboboxes
  - Auto-submitting the dashboard filter form on suggestion click (the user must still click "Actualizar busqueda")

## Decisions

### 1. Typed.js (vendored) over custom JS or CSS-only animation

**Decision:** Vendor `typed.min.js` (v2.x, ~7 KB) into `static/js/vendor/` and load it in the `{% block extra_js %}` of each template that contains a `[data-filter-widget]` (see Decision #6).

**Alternatives considered:**
- **Custom vanilla JS (~60-80 lines):** Would avoid any dependency, but Typed.js handles edge cases (cursor blink, backspace timing, shuffle, loop, per-string speed) that would require substantial custom testing. User chose Typed.js.
- **CSS-only `@keyframes steps()`:** Cannot dynamically generate strings from live API data; cannot make the element clickable (needs JS anyway); overly rigid.

**Rationale:** Typed.js is a well-maintained, single-purpose library with no transitive dependencies. Vendoring it gives deterministic availability (no CDN outage risk), matches the project's no-build-tool convention, and keeps the total JS cost under 10 KB.

### 2. Data source: Reuse the cached `/api/companies/filter-options/` response

**Decision:** The `search-suggestion.js` module will wait for the same `optionsPromise` that `combobox.js` already memoises, then generate 8-12 random "{Area} en {Location}..." strings from the result.

**Alternatives considered:**
- **Server-rendered JSON:** Would require a new template tag or view context variable. Adds template complexity for no bandwidth savings (the API is already cached).
- **Hardcoded list:** Would drift out of date as areas/locations change.

**Rationale:** Reusing the existing promise means zero additional API calls. The data is already on the page. To enable this, `combobox.js` will expose three things on a `window.FastJobFilter` namespace: (1) `optionsPromise` — the memoised promise, (2) `readyPromise` — a promise that resolves only after `initWidgets()` completes (so combobox containers have their `_addValue` methods available), and (3) `addValue(widget, comboboxType, value)` — a thin wrapper that finds the `[data-combobox="<type>"]` container within the widget and calls its internal `addValue` function. This avoids exposing the entire `initCombobox` internals while giving `search-suggestion.js` the hooks it needs without reaching into private closures.

**Implementation note:** The combobox IIFE is currently fully encapsulated (`(function () { ... })()`). Both `optionsPromise` (line 7) and `addValue` (line 105 of `initCombobox`) are private. The change will: (a) store each initialized combobox's `addValue` method on the container element (e.g. `container._addValue = addValue`), (b) expose `optionsPromise`, `readyPromise`, and `addValue(widget, type, value)` on `window.FastJobFilter`. The `readyPromise` is critical because `search-suggestion.js` must not call `addValue()` until after `initWidgets()` has finished — simply awaiting `optionsPromise` is insufficient since combobox initialisation happens inside the `.then()` callback.

### 3. Suggestion placement: subtitle under the section heading

**Decision:** The `<span data-search-suggestion>` element is placed immediately after the section `<h2>` (and after the subtitle `<p>` on the landing page), inside the existing heading container, positioned above the filter card.

**Rationale:** Placing it under the heading keeps visual proximity without disrupting the combobox layout. It reads as an invitation rather than an instruction.

### 4. Click-to-fill — uses Typed.js internal state, not DOM text parsing

**Decision:** The click handler uses Typed.js internal state (`typed.sequence[typed.arrayPos]`) to get the full current display string, then looks up the area/location values from a `stringMeta` array stored alongside the display strings. This is reliable regardless of where in the type/backspace cycle the click occurs — unlike parsing `el.textContent` which can catch mid-word fragments like "Aparatos e" instead of "Aparatos en Madrid...".

The widget element is found via `el.parentElement.querySelector('[data-filter-widget]')` rather than `el.closest('[data-filter-widget]')`, because on the landing page the suggestion span is a sibling of the filter-widget div, not a descendant.

**Rationale:** The user explicitly chose "clickable — fills filters on click" over auto-submit. The combobox's `onChange` callback already updates the count, so this is a minimally invasive integration.

### 5. Accessibility

**Decision:** The animated `<span>` carries `aria-hidden="true"` so screen readers skip it. The `prefers-reduced-motion` media query is checked at init time; if enabled, a single static suggestion string is rendered (no animation, no cursor, no Typed.js initialisation).

**Rationale:** The suggestion is decorative/supplementary. The combobox placeholders ("Escribe o elige un sector...") already communicate the type-to-search affordance to assistive technology.

## Risks / Trade-offs

- **Typed.js vendor maintenance:** Vendored files don't auto-update. Mitigation: pin the version in the filename (`typed.2.1.0.min.js`), add a comment in the template script tag with the version URL, and consider adding it to a future `package.json` for tracking.
- **Animation distraction:** A fast-cycling animation could annoy users who are already engaged with the comboboxes. Mitigation: pause animation on combobox focus; keep typeSpeed moderate (50 ms) and backDelay generous (2000 ms).
- **Edge case: few options:** If the database has 0-1 areas or locations, suggestion strings may be repetitive or nonsensical. Mitigation: fall back to a static hint if the combined option count is too low (< 2 areas or < 2 locations to form meaningful combos).
- **Race condition between suggestion module and combobox init:** The suggestion module needs both the options data AND fully-initialised comboboxes before it can set up click-to-fill. Mitigation: `window.FastJobFilter.readyPromise` resolves only after `initWidgets()` completes, so `search-suggestion.js` chains `readyPromise` rather than only `optionsPromise`.
- **CDN cache staleness:** After a deploy, the CDN may serve old JS for up to 24 hours. Mitigation: `?v=N` cache-busting query parameter on script URLs, incremented on each deploy that touches these files.

## Open Questions

### 6. Script loading strategy: child templates, not base.html

**Decision:** Typed.js and search-suggestion.js are loaded in the `{% block extra_js %}` of each template that contains a `[data-filter-widget]` (currently `home.html` and `dashboard/index.html`), in the order `combobox.js → typed.min.js → search-suggestion.js`. They are NOT loaded in `base.html`.

**Alternatives considered:**
- **Loading in `base.html` globally:** Simpler template change, but would cause script execution order problems since `combobox.js` loads via the child template's `{% block extra_js %}`. Putting `typed.min.js` and `search-suggestion.js` in `base.html` before the block means they execute before `combobox.js`, so `window.FastJobFilter` doesn't exist yet. Putting them after the block in `base.html` means they load on every page including ones with no filter widget (login, pricing, etc.), wasting ~7 KB.

**Rationale:** Loading all three scripts in the child template's `{% block extra_js %}` guarantees correct load order (`combobox.js` first, so `window.FastJobFilter` exists before `search-suggestion.js` runs). It also avoids loading Typed.js on pages that don't need it.

### 7. CDN cache-busting via query parameter

**Decision:** Dev/production static files are served via a DigitalOcean Spaces CDN with a 24-hour cache TTL. To ensure fresh static files are served after deployment, all three script URLs (`combobox.js`, `typed.min.js`, `search-suggestion.js`) carry a `?v=N` query parameter. The version `N` is incremented each time any of these files changes.

**Alternatives considered:**
- **CDN cache invalidation via DO API:** Requires DO API credentials and additional infrastructure. Not available in the current deployment pipeline.
- **Git-hash‑based versioning:** Would need a build step to inject the hash into templates. Overkill for the current project size.
- **No cache-busting:** Causes old JS to be served for up to 24 hours after a deploy, breaking new features that depend on updated JS.

**Rationale:** The `?v=N` approach is simple, reliable, and requires no extra infrastructure. It also serves as a clear indicator to developers that a static version bump is needed when deploying changes to any of these files.

- None at this time. The brainstorming session resolved all open questions (placement, interactivity, animation style, library choice).