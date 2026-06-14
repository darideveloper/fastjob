## Context

FastJob currently displays a Cookie Policy page mentioning a cookie control panel, but there is no cookie consent banner or control panel in the codebase. We need to implement a frontend cookie banner that complies with these declarations and lets users configure their preferences (Technical, Analytics, Personalization, Advertising) stored in the browser's local storage. In addition, we need to fix discrepancies in the Privacy Policy regarding the Microsoft `Mail.Send` scope disclosure.

## Goals / Non-Goals

**Goals:**
- Create an aesthetically pleasing, responsive Cookie Consent Banner at the bottom of the page.
- Persist cookie settings in `localStorage` under the key `fastjob_cookie_consent`.
- Provide granular configuration toggles for: Technical (locked/active), Analytics, Personalization, and Advertising.
- Expose a global JavaScript event or API (e.g. `window.FastJobConsent`) so future scripts can read consent choices.
- Implement a click handler on the Terms page to allow users to reopen the banner and change settings.
- Fix the missing Microsoft scope disclosure in the Privacy Policy page.

**Non-Goals:**
- Actually installing Google Analytics, advertising pixels, or other third-party tracking scripts in this change.
- Server-side storage of user cookie consent states.

## Decisions

### Decision 1: Storage Mechanism for Consent State
- **Option A:** Server-side sessions / Database flag
- **Option B:** Client-side cookies
- **Option C:** Client-side `localStorage` (Chosen)
- **Rationale:** `localStorage` is lightweight, does not bloat HTTP request headers, and can be read instantly by client-side Javascript. It is standard practice for modern static/dynamic cookie consent solutions.

### Decision 2: Location of Banner Logic & Integration
- **Option A:** Separate static file (`static/js/cookie-banner.js` + `static/css/...`)
- **Option B:** Embedded in `templates/cookie_banner.html` and included in `templates/base.html` (Chosen)
- **Rationale:** Embedding HTML, inline Tailwind (already loaded in base), and script in a single `cookie_banner.html` file keeps the feature self-contained, easy to insert or remove, and avoids adding HTTP requests for static assets on page load.

### Decision 3: Linking Terms Page Reference to Banner Modal
- **Option A:** Create a dedicated page for cookie settings.
- **Option B:** Bind click event on the Terms page's "panel de control de cookies" reference to trigger opening the main cookie banner in customization mode (Chosen).
- **Rationale:** Fits the requirement perfectly without adding route complexity, and provides an immediate interactive element directly inside the Terms page as stated in the legal copy.

## Risks / Trade-offs

- **[Risk]** The banner might cover important footer links or CTA buttons.
  - **Mitigation:** Style the banner as a floating bottom bar with a high `z-index` (e.g., `z-50`) and responsive padding to ensure content behind is readable, or add a dismiss slide-down animation.
- **[Risk]** Disabling optional cookies breaks future scripts.
  - **Mitigation:** The global `window.FastJobConsent` object will act as a gatekeeper. Future integrations (like Google Analytics) will check this object before initialization.

## Web Interface Guidelines Compliance

To comply with the Web Interface Guidelines:
1. **Accessibility**:
   - Every toggle switch and checkbox must be wrapped inside a `<label>` to share a single hit target without dead zones.
   - Any close or expand icon button must have an explicit `aria-label`.
   - Decorative icons must have `aria-hidden="true"`.
2. **Focus States**:
   - All interactive elements (buttons, toggles) must have visible focus indicators using Tailwind's `:focus-visible` (e.g., `focus-visible:ring-2 focus-visible:ring-brand focus-visible:outline-none`).
   - We must avoid raw `outline-none` / `outline: none` without providing a focus replacement.
3. **Animations**:
   - The banner entry and exit transitions must animate `opacity` and `transform` only.
   - We will list transition properties explicitly (e.g. `transition-[transform,opacity]`) and never use `transition: all`.
   - Transitions must respect user accessibility settings by disabling or reducing motion when `prefers-reduced-motion` is active.
4. **Typography**:
   - All text and loading strings must use curly quotes (`“` and `”`) and proper ellipses (`…`) instead of straight quotes and `...`.
   - Balance heading text with `text-wrap: balance` to prevent awkward line breaks on narrow viewports.
