"""
Health check endpoint for load balancers, uptime monitors, and container
orchestrators.

Returns 200 only if PostgreSQL and Redis cache are both reachable. Soft
configuration issues (e.g. Google project still in "Testing", missing imports
volume) are surfaced via a ``warnings`` array but do NOT degrade the response
status — those are deploy hygiene problems, not reasons to pull the instance
out of rotation.
"""
import logging
import os

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse

logger = logging.getLogger(__name__)


def imports_storage_check():
    """Inspect COMPANY_IMPORT_LOCAL_PATH and return a list of warning strings.

    The path must be present, a directory, and writable on every container that
    handles company-import uploads (web + celery_worker). A missing or
    read-only path causes the import view to fail to persist the batch file —
    surfacing the issue via /healthz lets the platform alert before operators
    hit it from the admin.
    """
    warnings = []
    path = getattr(settings, "COMPANY_IMPORT_LOCAL_PATH", None)
    if not path:
        return warnings
    if not os.path.exists(path):
        msg = f"COMPANY_IMPORT_LOCAL_PATH does not exist: {path}"
        warnings.append(msg)
        logger.warning("imports_storage_warning %s", msg)
    elif not os.path.isdir(path):
        msg = f"COMPANY_IMPORT_LOCAL_PATH is not a directory: {path}"
        warnings.append(msg)
        logger.warning("imports_storage_warning %s", msg)
    elif not os.access(path, os.W_OK):
        msg = f"COMPANY_IMPORT_LOCAL_PATH is not writable: {path}"
        warnings.append(msg)
        logger.warning("imports_storage_warning %s", msg)
    return warnings


def oauth_config_check():
    """Inspect OAuth-related settings and return a list of warning strings.

    Empty list = no warnings. Non-empty = something is set in a way that will
    silently break long-running token refresh.
    """
    warnings = []
    project_mode = getattr(settings, "GOOGLE_OAUTH_PROJECT_MODE", "production")
    if str(project_mode).lower() == "testing":
        msg = (
            "GOOGLE_OAUTH_PROJECT_MODE=testing — Google refresh tokens will "
            "expire after 7 days. Move the OAuth consent screen to Production."
        )
        warnings.append(msg)
        logger.warning("oauth_config_warning %s", msg)
    return warnings


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

    warnings = oauth_config_check() + imports_storage_check()

    ok = db_ok and cache_ok
    return JsonResponse(
        {
            "status": "ok" if ok else "degraded",
            "db": db_ok,
            "cache": cache_ok,
            "warnings": warnings,
        },
        status=200 if ok else 503,
    )
