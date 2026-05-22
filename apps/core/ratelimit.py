"""Client-IP resolution for rate limiting behind a reverse proxy.

FastJob runs behind Traefik (Coolify), so ``request.META["REMOTE_ADDR"]`` is
the proxy's container address — identical for every visitor. Using it as the
``django-ratelimit`` ``key="ip"`` bucket collapses the whole site into one
shared counter, so a normal traffic spike throttles everyone at once.

``get_client_ip`` recovers the real visitor IP from ``X-Forwarded-For`` in a
trust-bounded way and is wired into django-ratelimit via the
``RATELIMIT_IP_META_KEY`` setting, so every ``@ratelimit(key="ip", ...)``
limiter in the project keys on the actual visitor.
"""

import ipaddress

from django.conf import settings


def _remote_addr(request):
    # REMOTE_ADDR is set by the WSGI server on every real request; the
    # "0.0.0.0" fallback only guards against synthetic requests so the
    # caller is guaranteed a non-empty string.
    return request.META.get("REMOTE_ADDR") or "0.0.0.0"


def get_client_ip(request):
    """Return the real client IP for rate-limiting, never an empty string.

    ``X-Forwarded-For`` is *appended* to by every hop, so its left-hand
    entries are client-controlled and untrustworthy. Only the rightmost
    ``TRUSTED_PROXY_HOPS`` entries are contributed by infrastructure we
    operate; the genuine client is the entry the outermost trusted proxy
    saw — ``xff[-TRUSTED_PROXY_HOPS]``.

    For the current Coolify/Traefik deployment there is exactly one trusted
    hop (default ``1``), so the client is ``xff[-1]``. Raise
    ``TRUSTED_PROXY_HOPS`` if a CDN is later placed in front of Traefik.

    Falls back to ``REMOTE_ADDR`` whenever the header is missing, has fewer
    entries than the trusted-hop count (malformed / spoofed-short), or the
    selected entry is not a valid IP address.
    """
    hops = getattr(settings, "TRUSTED_PROXY_HOPS", 1)

    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    parts = [p.strip() for p in forwarded.split(",") if p.strip()]

    # Fewer entries than trusted proxies means the chain is not what we
    # expect — do not trust any of it.
    if len(parts) < hops or hops < 1:
        return _remote_addr(request)

    candidate = parts[-hops]
    try:
        ipaddress.ip_address(candidate)
    except ValueError:
        return _remote_addr(request)

    return candidate
