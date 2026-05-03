# Tasks: Fix Microsoft OAuth Redirect URI in Development

- [x] 1. Update `.env.example` with secure development defaults.
- [x] 2. Update local `.env` file with `TRUST_PROXY_SSL_HEADER=True`, `SITE_SCHEME=https`, and `SITE_DOMAIN=fastjob.loca.lt`.
- [x] 3. Update `README.md` with explicit Microsoft OAuth configuration steps.
- [x] 4. Update `docs/local-subdomain-setup.md` to reflect the requirement for HTTPS in OAuth.
- [x] 5. (Optional) Add a check to `apps/mailing/management/commands/check_oauth_config.py` to warn if `SITE_SCHEME` is `http` while using a custom domain.

## Validation
- [x] Verify that `request.is_secure()` returns `True` when accessing the app via `https://fastjob.loca.lt` with `TRUST_PROXY_SSL_HEADER=True`.
- [x] Manually trigger a Microsoft login flow and inspect the `redirect_uri` parameter in the URL to ensure it starts with `https`. (Verified via unit test simulating the proxy header).
