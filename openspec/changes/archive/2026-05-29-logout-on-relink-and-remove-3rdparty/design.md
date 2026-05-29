## Context

The warning banner button on the dashboard ("Vincular ahora") currently points to `/accounts/login/`. Since logged-in users are automatically redirected away from `/accounts/login/` back to the dashboard, they cannot use it to re-establish expired or missing OAuth credentials. Additionally, users can currently access `/accounts/3rdparty/` to manually unlink their Google or Microsoft OAuth connections, which breaks FastJob's core background mailing capabilities and halts active campaigns.

## Goals / Non-Goals

**Goals:**
- Update the "Vincular ahora" warning button to link directly to `/accounts/logout/`. This forces a session reset so the user can re-authenticate via Google or Microsoft, creating fresh OAuth tokens.
- Disable manual unlinking by completely unmounting the `/accounts/3rdparty/` routes.
- Delete unused template files and clean up the test suite to match these changes.

**Non-Goals:**
- Modifying how Google/Microsoft OAuth logins or callback URLs are handled (they will remain active).
- Changing Django Admin's ability to view or manage social accounts.

## Decisions

### 1. Direct "Vincular ahora" to `/accounts/logout/`
- **Decision**: Update the warning banner link in `templates/dashboard/index.html` from `/accounts/login/` to `{% url 'account_logout' %}`.
- **Rationale**: When users click "Vincular ahora", they will be taken to the styled logout confirmation screen. Upon clicking "Cerrar sesión", their Django session is cleared, and they are redirected to `/` or the login screen. They can then log back in using the OAuth buttons, which automatically re-authenticates and restores the missing/expired social account credentials.
- **Alternatives considered**: 
  - *Custom auto-logout link*: Trigger a POST logout immediately without confirmation. This was rejected because the logout confirmation screen provides a smoother user experience and standard web security behavior.

### 2. Unmounting `/accounts/3rdparty/` URLs and Defensive Routing
- **Decision**: Remove `path("accounts/3rdparty/", include("allauth.socialaccount.urls")),` from `config/urls.py` and register a redirect named `"socialaccount_signup"` to `/accounts/login/` using Django's `RedirectView`.
- **Rationale**: Unmounting this routing module completely removes the connections management pages. However, because `django-allauth`'s internal codebase might try to resolve/reverse `socialaccount_signup` when processing social logins or handling validation errors, defining a defensive dummy fallback prevents `NoReverseMatch` crashes.
- **Alternatives considered**:
  - *Overriding the template with a blank screen or disabled banner*: Rejected because keeping the URLs mounted increases the attack surface and leaves dead routes in the app.

## Risks / Trade-offs

- **[Risk]** Removing `allauth.socialaccount.urls` might break OAuth login or callback endpoints.
  - *Mitigation*: The OAuth login and callback endpoints for Google and Microsoft are mounted separately in `config/urls.py` via `allauth.socialaccount.providers.google.urls` and `allauth.socialaccount.providers.microsoft.urls` respectively. These remain fully intact and operational.
- **[Risk]** Removing the unlinking pages might break the test suite (e.g. `test_socialaccount_connections_route_preserved`).
  - *Mitigation*: We will modify the test suite to assert that `/accounts/3rdparty/` and `/accounts/3rdparty/connections/` correctly raise a `Resolver404` and that `socialaccount_signup` redirects safely to `account_login`.

