## 1. Warn Banner Update

- [x] 1.1 In `templates/dashboard/index.html`, modify the warning banner's "Vincular ahora" action button `href` attribute to point to `{% url 'account_logout' %}` instead of `/accounts/login/`.

## 2. Remove Unlinking Routes & Dead Code

- [x] 2.1 In `config/urls.py`, remove `path("accounts/3rdparty/", include("allauth.socialaccount.urls")),` and add a defensive `socialaccount_signup` redirect pointing to `/accounts/login/` via `RedirectView.as_view(pattern_name="account_login", permanent=False)`.
- [x] 2.2 Delete the template file `templates/socialaccount/connections.html`.

## 3. Update Test Suite & Verify Coverage

- [x] 3.1 In `apps/accounts/tests/test_url_surface.py`, replace `test_socialaccount_connections_route_preserved` with:
  * A test asserting that `/accounts/3rdparty/` raises a `Resolver404` (since it is unmounted).
  * A test asserting that `socialaccount_signup` reverses correctly to `/accounts/signup/` (or redirects safely to `/accounts/login/`).
- [x] 3.2 Run the test suite (`pytest`) to verify all tests pass successfully.
