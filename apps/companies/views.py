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
    area = request.GET.get("area", "").strip()
    location = request.GET.get("location", "").strip()

    allowed_areas = {a.lower() for a in options["areas"]}
    allowed_locations = {loc.lower() for loc in options["locations"]}

    if area and area.lower() not in allowed_areas:
        return JsonResponse({"error": "invalid_filter"}, status=400)
    if location and location.lower() not in allowed_locations:
        return JsonResponse({"error": "invalid_filter"}, status=400)

    count = get_company_count(area or None, location or None)
    return JsonResponse({"count": count})
