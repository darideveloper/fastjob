# Proposal: Fix Microsoft OAuth Redirect URI in Development

## Problem
When using `localtunnel` for local development, Microsoft OAuth login fails because the generated `redirect_uri` uses the `http` scheme (e.g., `http://fastjob.loca.lt/...`). Microsoft Entra ID strictly requires `https` for all redirect URIs on non-localhost domains. This happens because Django is unaware it is behind an HTTPS-terminating proxy and thus reports `is_secure() == False`.

## Proposed Solution
Enable Django to recognize the `X-Forwarded-Proto` header sent by `localtunnel` and other proxies. This will ensure `build_absolute_uri()` correctly generates `https` links.

### Changes
1.  **Environment Configuration (`.env` and `.env.example`):**
    *   Set `TRUST_PROXY_SSL_HEADER=True` to enable `SECURE_PROXY_SSL_HEADER` in `settings.py`.
    *   Update `SITE_DOMAIN` to `fastjob.loca.lt` and `SITE_SCHEME` to `https` to provide sane defaults for development.
2.  **Documentation:**
    *   Update `README.md` and `docs/local-subdomain-setup.md` to emphasize that `https` is mandatory for Microsoft OAuth and explain how to configure it in the Azure Portal.

## Impact
*   **Low Risk:** This change only affects how Django perceives the connection protocol when a specific environment variable is set. It is already gated by `config("TRUST_PROXY_SSL_HEADER", default=False, cast=bool)` in `settings.py`.
*   **Improved Dev Experience:** Developers can use Microsoft OAuth with `localtunnel` without scheme mismatch errors.
