## 1. Cookie Consent Banner UI & Logic

- [x] 1.1 Create `templates/cookie_banner.html` with a highly polished Tailwind overlay containing the Cookie Consent Banner, customization panel toggles, and buttons for Accept All, Reject All, and Save.
  - [x] 1.1.1 Accessibility: Wrap each toggle switch/checkbox input in a `<label>` to share a single hit target without dead zones.
  - [x] 1.1.2 Focus States: Ensure all buttons and inputs have visible focus rings using `:focus-visible` (e.g. `focus-visible:ring-2 focus-visible:ring-brand focus-visible:outline-none`). Do not use raw `outline-none`.
  - [x] 1.1.3 Typography: Use proper curly quotes (`“`/`”`), balanced headings (`text-wrap: balance`), and correct ellipses (`…` instead of `...`).
  - [x] 1.1.4 Screen Readers: Add `aria-hidden="true"` to any decorative icons/SVGs and ensure buttons have descriptive names.
- [x] 1.2 Implement client-side JavaScript inside `templates/cookie_banner.html` that manages loading, showing, and saving cookie preferences under `localStorage` key `fastjob_cookie_consent`.
  - [x] 1.2.1 Motion: Animate `transform` and `opacity` only (no `transition: all`, use explicit classes like `transition-[transform,opacity]`).
  - [x] 1.2.2 Reduced Motion: Implement a check for `@media (prefers-reduced-motion: reduce)` to disable or simplify transition animations.
- [x] 1.3 Expose a global `window.FastJobConsent` object containing boolean values for `essential`, `analytics`, `personalization`, and `advertising`.
- [x] 1.4 Include `{% include "cookie_banner.html" %}` in `templates/base.html` immediately before the closing `</body>` tag.



## 2. Legal Page Discrepancy Fixes

- [x] 2.1 Modify Section 3 of `templates/legal/privacy.html` to declare the Microsoft `Mail.Send` scope for outbound emails alongside Google `gmail.send`.
- [x] 2.2 Modify `templates/legal/terms.html` to convert the "panel de control de cookies" text reference into a clickable button/link with ID `open-cookie-settings`.
- [x] 2.3 Add global event handling so that clicking `#open-cookie-settings` re-displays the Cookie Consent customization modal.



## 3. Verification & Testing

- [x] 3.1 Update test cases in `apps/core/tests/test_views.py` to assert that the Privacy Policy contains references to Microsoft's `Mail.Send` permission.
- [x] 3.2 Run the full test suite using `pytest` to verify all tests pass.


