from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django_ratelimit.decorators import ratelimit

from .queries import get_company_count, get_filter_options


def _invalid_filter_response():
    """400 for a filter value outside the allowed-options whitelist.

    Marked `no-store` so a transient bad request is never cached by a
    browser or shared cache.
    """
    response = JsonResponse({"error": "invalid_filter"}, status=400)
    response["Cache-Control"] = "no-store"
    return response


# Rates are resolved per request (django-ratelimit accepts a callable) rather
# than captured at import time, so the threshold stays operator-configurable
# and is overridable in tests via @override_settings.
def _filter_options_rate(group, request):
    return settings.RATELIMIT_FILTER_OPTIONS


def _filter_count_rate(group, request):
    return settings.RATELIMIT_FILTER_COUNT


@require_GET
@ratelimit(key="ip", rate=_filter_options_rate, block=True)
def filter_options_view(request):
    options = get_filter_options()
    response = JsonResponse(options)
    # The taxonomy is identical for every visitor and changes rarely, so let
    # browsers and shared caches serve it without hitting the origin — and
    # without spending the per-IP rate-limit budget on every page view.
    # Aligned with the 5-minute server-side cache in get_filter_options().
    response["Cache-Control"] = "public, max-age=300"
    return response


@require_GET
@ratelimit(key="ip", rate=_filter_count_rate, block=True)
def companies_count_view(request):
    options = get_filter_options()
    areas = [v.strip() for v in request.GET.getlist("area") if v.strip()]
    locations = [v.strip() for v in request.GET.getlist("location") if v.strip()]

    allowed_areas = {a.strip().lower() for a in options["areas"]}
    allowed_locations = {loc.strip().lower() for loc in options["locations"]}

    for area in areas:
        if area.strip().lower() not in allowed_areas:
            return _invalid_filter_response()
    for location in locations:
        if location.strip().lower() not in allowed_locations:
            return _invalid_filter_response()

    count = get_company_count(areas or None, locations or None)
    response = JsonResponse({"count": count})
    # The count is a query-keyed integer with no per-user data, so a shared
    # cache may serve it. Aligned with the 60-second server-side cache in
    # get_company_count().
    response["Cache-Control"] = "public, max-age=60"
    return response
