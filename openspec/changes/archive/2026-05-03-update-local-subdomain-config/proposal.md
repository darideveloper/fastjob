# Proposal: Update Environment Variables for Local Subdomain

## Summary
Update the application configuration and environment variable templates to support the `https://fastjob.localhost` subdomain for local development. This includes enforcing the use of environment variables for `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, and `SITE_DOMAIN` by removing their hardcoded default values in `config/settings.py`.

## Motivation
Using a structured subdomain like `fastjob.localhost` for local development provides several benefits:
1. **RFC 6761 Compliance**: The `.localhost` TLD is reserved for loopback and resolved locally by modern browsers (Chrome, Firefox).
2. **Isolation**: Prevents cookie and session leakage between different projects running on `localhost`.
3. **Subdomain Support**: Allows testing features that rely on subdomain routing or specific hostnames without external tunnels or `/etc/hosts` modifications.
4. **HTTPS Emulation**: Facilitates local development behind a proxy (like Caddy or Nginx) using the `fastjob.localhost` domain.
5. **Configuration Rigor**: Removing defaults in `settings.py` ensures that the application is always explicitly configured via environment variables, reducing the risk of accidental misconfiguration in different environments.

## Scope
- `config/settings.py`: Remove hardcoded default values for `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, and `SITE_DOMAIN`.
- `.env.example`: Update example values to include `fastjob.localhost`.
- `.env`: Update the active environment file to include the new domain.
- `docs/local-subdomain-setup.md`: Update documentation to reflect the preference for `.localhost`.
