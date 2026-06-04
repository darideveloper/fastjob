## Why

When a user cancels the Microsoft or Google login screen, the OAuth callback receives an `error=access_denied` parameter. The `django-allauth` application maps this to `AuthError.CANCELLED` and attempts to redirect the user to a page named `socialaccount_login_cancelled`. However, because `allauth.socialaccount.urls` was unmounted to prevent user connection management, this named URL pattern is missing, resulting in a server-side `NoReverseMatch` crash (500 error) instead of showing the custom cancellation page.

## What Changes

- Add routing for the two missing social login views: `socialaccount_login_cancelled` and `socialaccount_login_error`.
- Ensure they render their corresponding existing custom templates (`templates/socialaccount/login_cancelled.html` and `templates/socialaccount/authentication_error.html`).
- Ensure no other connections management endpoints (e.g. unlinking) are exposed, keeping the OAuth-only behavior intact.

## Capabilities

### New Capabilities
<!-- Capabilities being introduced. Replace <name> with kebab-case identifier (e.g., user-auth, data-export, api-rate-limiting). Each creates specs/<name>/spec.md -->

### Modified Capabilities
<!-- Existing capabilities whose REQUIREMENTS are changing (not just implementation).
     Only list here if spec-level behavior changes. Each needs a delta spec file.
     Use existing spec names from openspec/specs/. Leave empty if no requirement changes.
-->
- `accounts`: Ensure the custom templates for cancelled logins and authentication errors are reachable via standard URL mapping rather than throwing `NoReverseMatch` exceptions when accessed.

## Impact

- **Affected code**: `config/urls.py` will have the two missing paths added.
- **Affected tests**: `apps/accounts/tests/test_url_surface.py` will be updated with assertions to ensure `socialaccount_login_cancelled` and `socialaccount_login_error` resolve successfully.
