# Security

ResumeLink's threat model centres on two high-value targets: OAuth tokens (give email-send access to users' inboxes) and CV files (private PII). Everything else is standard Django hardening.

---

## Threat model

| Asset | Threat | Mitigation |
|---|---|---|
| OAuth access tokens | Stolen from DB → attacker can send email as user | DB-level encryption (hosting provider), tokens short-lived (~1h) |
| OAuth refresh tokens | Stolen → long-lived access | Same DB encryption; revoke via Google/Microsoft account settings |
| CV PDFs | Public exposure | Private S3 bucket; pre-signed URLs (5 min TTL); never served directly |
| CV download links (`/cv/<uuid>/`) | Scraped/brute-forced | 122-bit UUID entropy; 30 req/h/IP rate limit |
| Unsubscribe links | Replay / abuse | 10 req/h/IP rate limit; `get_or_create` is idempotent |
| Stripe webhook | Fake payment event to grant credits | HMAC signature via `stripe.Webhook.construct_event` |
| Django admin | Unauthorized access | `is_staff` gate; recommended: IP-restrict at load balancer |
| Session cookies | Hijacking | `SESSION_COOKIE_SECURE=True` in prod; `HttpOnly` by default |

---

## Rate limiting

`django-ratelimit` protects the two public endpoints that accept unauthenticated traffic:

| Endpoint | Rate | Key | Decorator |
|---|---|---|---|
| `/cv/<uuid>/` | 30/hour | IP | `@ratelimit(key="ip", rate="30/h", block=True)` |
| `/unsubscribe/<uuid>/` | 10/hour | IP | `@ratelimit(key="ip", rate="10/h", block=True)` |

When the limit is exceeded, `django-ratelimit` raises a `Ratelimited` exception. `RatelimitMiddleware` (`apps/mailing/middleware.py`) converts it to HTTP 429 with a plain-text body in Spanish.

**Why 429 and not 403:** 403 means "authenticated but forbidden" — CDNs and monitoring tools treat it differently from "client is throttling." 429 is the correct semantic for rate-limiting per RFC 6585.

Rate limiting requires the Redis cache backend (`CACHE_REDIS_URL`). If Redis is down, `IGNORE_EXCEPTIONS=True` in the cache config means rate limiting silently degrades (requests pass through). This is an availability-over-security trade-off — the alternative would be to 503 every request when Redis is down.

To disable rate limiting in tests or local dev: set `RATELIMIT_ENABLE=False` in `.env`.

---

## Security headers

All configured via environment variables in `config/settings.py` so local dev is unaffected. Flip all to `True`/non-zero once behind HTTPS in production.

| Header / Setting | Env var | Production value |
|---|---|---|
| HTTPS redirect | `SECURE_SSL_REDIRECT` | `True` |
| Session cookie over HTTPS only | `SESSION_COOKIE_SECURE` | `True` |
| CSRF cookie over HTTPS only | `CSRF_COOKIE_SECURE` | `True` |
| HSTS max-age (seconds) | `SECURE_HSTS_SECONDS` | `31536000` (1 year) |
| HSTS include subdomains | `SECURE_HSTS_INCLUDE_SUBDOMAINS` | `True` |
| HSTS preload | `SECURE_HSTS_PRELOAD` | `True` (one-way door — submit to preload list only when ready) |
| `X-Content-Type-Options: nosniff` | hardcoded | Always `True` |
| `Referrer-Policy` | hardcoded | `strict-origin-when-cross-origin` |
| `X-Frame-Options: DENY` | hardcoded | Always |
| Trusted CSRF origins | `CSRF_TRUSTED_ORIGINS` | `https://yourdomain.com` |

### Proxy SSL header

If Django runs behind a TLS-terminating proxy (DigitalOcean App Platform, Nginx, Heroku):

```env
TRUST_PROXY_SSL_HEADER=True
```

This sets `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")`, allowing Django to detect HTTPS from the `X-Forwarded-Proto` header.

---

## CSRF

Django's default CSRF middleware is enabled. Dashboard, payments, and filter forms all submit via POST with the CSRF token embedded in the form. The Stripe webhook is `@csrf_exempt` — Stripe's HMAC signature serves the same purpose.

---

## Static file serving

Static files are served by `whitenoise` directly from the Django process (no separate Nginx needed). Whitenoise serves pre-compressed files and sets long-lived `Cache-Control` headers. It does not serve files from `MEDIA_ROOT` — media (CVs) goes directly to DigitalOcean Spaces.

---

## Token storage security

OAuth tokens are stored in `allauth`'s `SocialToken` table as plain text. Django's ORM does not encrypt them. Security relies on:

1. **DB-level encryption** from your hosting provider (DigitalOcean Managed PostgreSQL encrypts at rest by default).
2. **Access control** — only the Django process has DB credentials.
3. **Token short-livedness** — access tokens expire in ~1 hour. Refresh tokens are invalidated when the user revokes access in their Google/Microsoft account.

If you need application-level encryption for the tokens, consider [django-cryptography](https://django-cryptography.readthedocs.io) `EncryptedCharField` as a drop-in replacement for the `SocialToken` fields (requires a custom allauth adapter).

---

## DigitalOcean Spaces IAM

The Spaces access key used by Django should be scoped to a **single bucket** with the minimum permissions:
- `s3:GetObject`
- `s3:PutObject`
- `s3:DeleteObject`

Not account-wide. If the key is leaked, the blast radius is limited to the CV bucket.

---

## Django `SECRET_KEY`

Used for session signing, CSRF tokens, and password reset links. It must be:
- Long (50+ characters).
- Random.
- Never committed to version control.
- Rotated if compromised (invalidates all sessions and CSRF tokens — a brief disruption, not a catastrophe).

Generate one: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`.

---

## Known limitations (P2/P3)

| Limitation | Severity | Notes |
|---|---|---|
| No application-level token encryption | Medium | Relies entirely on DB disk encryption |
| No CV content scanning (malware/AV) | Low | We trust users; P3 item: ClamAV integration |
| No brute-force protection on `/admin/` login | Low | Mitigate by IP-restricting `/admin/` at the load balancer |
| GDPR deletion flow incomplete | Medium | `User.cv_file.delete()` not called on account deletion; see `log.md` |

---

## Related docs

- [`authentication.md`](authentication.md) — OAuth token storage details.
- [`cv-management.md`](cv-management.md) — S3 security model.
- [`payments.md`](payments.md) — Stripe webhook signature verification.
- [`monitoring.md`](monitoring.md) — error tracking via Sentry.
