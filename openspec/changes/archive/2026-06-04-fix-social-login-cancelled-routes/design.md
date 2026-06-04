## Context

The fastjob application is configured as an OAuth-only site, using `django-allauth` for user authentication. In [config/urls.py](file:///develop/django/fastjob/config/urls.py), the `allauth.socialaccount.urls` configuration is omitted to avoid exposing routes for managing multiple linked accounts or unlinking them. However, when users decline authorization on Microsoft or Google login screens, allauth redirects to the callback endpoint with `error=access_denied` which is handled as an authentication cancellation. The cancellation handler tries to reverse `socialaccount_login_cancelled`, which causes a `NoReverseMatch` crash (500 Internal Server Error) instead of displaying the custom cancellation page that has already been created at `templates/socialaccount/login_cancelled.html`.

## Goals / Non-Goals

**Goals:**
- Correctly resolve `socialaccount_login_cancelled` and `socialaccount_login_error` so they render their respective customized templates instead of throwing server errors.
- Ensure that this routing is active for both Microsoft and Google OAuth providers.
- Maintain existing visual identity and branding guidelines in the rendered templates.

**Non-Goals:**
- Do not mount other routes from `allauth.socialaccount.urls` that allow user connections management (unlinking or multi-social-linking accounts).
- Do not support username/password registration or standard password-reset urls.

## Decisions

### Decision 1: Mount specific views individually in the URL routing config
- **Rationale**: Since we only want to expose cancellation and error pages, importing and mounting `login_cancelled` and `login_error` from `allauth.socialaccount.views` is the cleanest and most targeted solution. It completely avoids mounting unnecessary routes like `socialaccount_connections`.
- **Alternatives Considered**: 
  - Mounting the entire `allauth.socialaccount.urls` at `/accounts/3rdparty/` is rejected because it would expose unlinking endpoints (`/accounts/3rdparty/connections/`), violating the "OAuth-only with single linked account" constraint.
  - Using `RedirectView` to redirect both cancellation and error routes directly to `/accounts/login/` was rejected because the design specification contains specific, user-friendly cancellation/error templates designed to help users retry.

## Risks / Trade-offs

- **[Risk]**: Accidental exposure of other allauth social account endpoints.
  - **Mitigation**: Expose only the specific function/class views (`login_cancelled` and `login_error`) under the correct names, keeping all other paths unmounted. Assert this in URL surface tests.
