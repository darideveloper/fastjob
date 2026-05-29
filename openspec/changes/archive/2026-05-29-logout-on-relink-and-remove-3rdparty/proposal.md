## Why

When a user's OAuth connection expires, or if their user account is created manually via the admin panel without a linked social account, the background mailing engine automatically pauses their campaign with an `"expired"` reason and displays a banner on the dashboard with a "Vincular ahora" button. Because this button currently points to `/accounts/login/` and the user is already authenticated in Django, clicking it triggers a redirection loop back to the dashboard, rendering the button non-functional.

Furthermore, the `/accounts/3rdparty/` pages allow users to view and manually unlink their Google/Microsoft social accounts. Since FastJob is a pure OAuth-only application where campaigns rely entirely on active social account connections, unlinking an account breaks the core system flow. Preventing the user from manually unlinking accounts makes the system more robust and secure.

## What Changes

- **Logout Redirect on Relink**: Modify the "Vincular ahora" button in the dashboard warning banner to point to `/accounts/logout/` instead of `/accounts/login/`. This prompts the user to log out and log back in, which triggers django-allauth to automatically re-authenticate and restore the missing/expired social account credentials.
- **Remove Account Unlinking**: Remove all capabilities for clients to manually unlink their social accounts by completely unmounting the `/accounts/3rdparty/` (`allauth.socialaccount.urls`) routes.
- **Defensive Routing Safeguard**: To prevent potential `NoReverseMatch` runtime errors inside `django-allauth` (which might attempt to resolve the `socialaccount_signup` URL under rare validation error cases), define a dummy redirect route for `socialaccount_signup` in `config/urls.py` that redirects to `/accounts/login/` (matching the existing strategy for `account_signup`).
- **Dead Code Clean-Up**: Delete the `socialaccount/connections.html` template and clean up all associated tests that check `/accounts/3rdparty/` URL resolution.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `accounts`: Update oauth connection relinking to flow through the logout sequence, and remove the ability to unlink/disconnect social accounts.

## Impact

- **Templates**: 
  - `templates/dashboard/index.html` (update "Vincular ahora" link)
  - `templates/socialaccount/connections.html` (delete file)
- **URL Configuration**:
  - `config/urls.py` (remove `accounts/3rdparty/` route, add defensive `socialaccount_signup` dummy redirect)
- **Test Suite**:
  - `apps/accounts/tests/test_url_surface.py` (replace assertion for `socialaccount_connections` with `Resolver404` assertion, and add assertion for `socialaccount_signup` redirect)

