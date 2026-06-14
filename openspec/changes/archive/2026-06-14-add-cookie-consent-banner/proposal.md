## Why

The application currently has inconsistencies between its legal documentation and its actual codebase: the Terms of Service claims a cookie control panel exists to manage cookies (such as analytics or advertising) that aren't actually set by FastJob, and the Privacy Policy is missing the Microsoft `Mail.Send` scope disclosure. This change fixes these discrepancies and implements a fully functional, highly polished cookie consent banner with options for future expansions (e.g., Google Analytics).

## What Changes

- Add a modular, highly aesthetic Cookie Consent Banner (`templates/cookie_banner.html`) supporting multiple consent tiers (Essential, Analytics, Personalization, Advertising) with user choices stored in local storage/cookie.
- Inject the Cookie Consent Banner into `templates/base.html` so it displays for new visitors and executes consent-dependent logic.
- Update `templates/legal/terms.html` to link the "panel de control de cookies" reference directly to a button/event that reopens the cookie consent banner, making the legal text true.
- Update `templates/legal/privacy.html` to explicitly disclose Microsoft's `Mail.Send` scope alongside Google's `gmail.send` scope.

## Capabilities

### New Capabilities

*(None)*

### Modified Capabilities

- `legal`: The requirements for legal information are updated to include Microsoft email scopes and interactive cookie management.

## Impact

- Affected templates: `templates/base.html`, `templates/legal/terms.html`, `templates/legal/privacy.html`.
- New template: `templates/cookie_banner.html`.
- Affected javascript: Added client-side script in `templates/cookie_banner.html` (or separate static file) for managing consent states.
- Affected tests: `apps/core/tests/test_views.py`.
