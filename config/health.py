"""
Health check endpoint for load balancers, uptime monitors, and container
orchestrators. Returns 200 only if PostgreSQL and Redis cache are both reachable.
"""
import logging

from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse

logger = logging.getLogger(__name__)


def healthz(request):
    db_ok = False
    cache_ok = False

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        db_ok = True
    except Exception as exc:
        logger.warning("healthz: DB check failed: %s", exc)

    try:
        cache.set("healthz:ping", "ok", timeout=5)
        cache_ok = cache.get("healthz:ping") == "ok"
    except Exception as exc:
        logger.warning("healthz: cache check failed: %s", exc)

    ok = db_ok and cache_ok
    return JsonResponse(
        {
            "status": "ok" if ok else "degraded",
            "db": db_ok,
            "cache": cache_ok,
        },
        status=200 if ok else 503,
    )
