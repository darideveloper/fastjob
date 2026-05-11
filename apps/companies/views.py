from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django_ratelimit.decorators import ratelimit

from .queries import get_company_count, get_filter_options


@require_GET
@ratelimit(key="ip", rate="30/h", block=True)
def filter_options_view(request):
    options = get_filter_options()
    return JsonResponse(options)


@require_GET
@ratelimit(key="ip", rate="60/h", block=True)
def companies_count_view(request):
    options = get_filter_options()
    areas = [v.strip() for v in request.GET.getlist("area") if v.strip()]
    locations = [v.strip() for v in request.GET.getlist("location") if v.strip()]

    allowed_areas = {a.strip().lower() for a in options["areas"]}
    allowed_locations = {loc.strip().lower() for loc in options["locations"]}

    for area in areas:
        if area.strip().lower() not in allowed_areas:
            return JsonResponse({"error": "invalid_filter"}, status=400)
    for location in locations:
        if location.strip().lower() not in allowed_locations:
            return JsonResponse({"error": "invalid_filter"}, status=400)

    count = get_company_count(areas or None, locations or None)
    return JsonResponse({"count": count})
