## 1. Routing Configuration

- [x] 1.1 Import `login_cancelled` and `login_error` from `allauth.socialaccount.views` in `config/urls.py`.
- [x] 1.2 Map `accounts/social/login/cancelled/` to `login_cancelled` view with name `socialaccount_login_cancelled` in `config/urls.py`.
- [x] 1.3 Map `accounts/social/login/error/` to `login_error` view with name `socialaccount_login_error` in `config/urls.py`.

## 2. Verification and Tests

- [x] 2.1 Add unit tests to `apps/accounts/tests/test_url_surface.py` asserting that `socialaccount_login_cancelled` and `socialaccount_login_error` reverse and resolve correctly.
- [x] 2.2 Run pytest to ensure all accounts and URL surface tests pass successfully.
