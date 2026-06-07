from hashlib import sha1

from django.core.cache import cache

OPTIONS_CACHE_KEY = "companies:filter-options:v1"
COUNT_VERSION_KEY = "companies:count:version"
AVAILABLE_FILTERS_TTL = 60  # 1 minute (same as count)
OPTIONS_TTL = 300  # 5 minutes
COUNT_TTL = 60  # 1 minute


def get_filter_options():
    """Return {"areas": [...], "locations": [...], "sub_areas": [...]} from Managed Taxonomy, cached 5 min."""
    from .models import Area, Location, SubArea

    cached = cache.get(OPTIONS_CACHE_KEY)
    if cached is not None:
        return cached

    result = {
        "areas": list(Area.objects.values_list("name", flat=True).order_by("name")),
        "locations": list(Location.objects.values_list("name", flat=True).order_by("name")),
        "sub_areas": list(SubArea.objects.values_list("name", flat=True).order_by("name")),
    }
    cache.set(OPTIONS_CACHE_KEY, result, OPTIONS_TTL)
    return result


def matching_companies_qs(areas=None, locations=None, sub_areas=None):
    """Return a Company QS filtered by area/location/sub-area names.

    Empty/None values mean 'no filter on that field'. Callers are responsible
    for applying any additional exclusions (blacklist, cooldown, etc.).
    """
    from .models import Company

    qs = Company.objects.all()
    if areas:
        if hasattr(areas, "values_list"):
            areas = list(areas.values_list("name", flat=True))
        elif not isinstance(areas, (list, tuple)):
            areas = [areas]
        areas = [str(a).lower() for a in areas]
        qs = qs.filter(area__name__in=areas)

    if locations:
        if hasattr(locations, "values_list"):
            locations = list(locations.values_list("name", flat=True))
        elif not isinstance(locations, (list, tuple)):
            locations = [locations]
        locations = [str(l).lower() for l in locations]
        qs = qs.filter(location__name__in=locations)

    if sub_areas:
        if hasattr(sub_areas, "values_list"):
            sub_areas = list(sub_areas.values_list("name", flat=True))
        elif not isinstance(sub_areas, (list, tuple)):
            sub_areas = [sub_areas]
        sub_areas = [str(s).lower() for s in sub_areas]
        qs = qs.filter(sub_area__name__in=sub_areas)

    return qs


def get_company_count(areas=None, locations=None, sub_areas=None):
    """Count companies matching area/location/sub-area filters, with 60 s cache."""
    area_key = ""
    if areas:
        if hasattr(areas, "values_list"):
            areas = list(areas.values_list("name", flat=True))
        elif not isinstance(areas, (list, tuple)):
            areas = [areas]
        area_key = ",".join(sorted(str(a) for a in areas))

    loc_key = ""
    if locations:
        if hasattr(locations, "values_list"):
            locations = list(locations.values_list("name", flat=True))
        elif not isinstance(locations, (list, tuple)):
            locations = [locations]
        loc_key = ",".join(sorted(str(l) for l in locations))

    sub_key = ""
    if sub_areas:
        if hasattr(sub_areas, "values_list"):
            sub_areas = list(sub_areas.values_list("name", flat=True))
        elif not isinstance(sub_areas, (list, tuple)):
            sub_areas = [sub_areas]
        sub_key = ",".join(sorted(str(s) for s in sub_areas))

    version = cache.get(COUNT_VERSION_KEY, 0)
    raw_key = f"{version}|{area_key}|{loc_key}|{sub_key}"
    cache_key = f"companies:count:v1:{sha1(raw_key.encode()).hexdigest()}"

    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    count = matching_companies_qs(areas, locations, sub_areas).count()
    cache.set(cache_key, count, COUNT_TTL)
    return count


def get_available_filters(areas=None, locations=None, sub_areas=None):
    """Return available filter options constrained by cross-dimensional filtering.

    Each dimension is constrained by the other two dimensions:
    - available_areas: areas with companies in the selected locations AND selected sub_areas
    - available_locations: locations with companies in the selected areas AND selected sub_areas
    - available_sub_areas: sub_areas with companies in the selected areas AND selected locations

    When no filters are selected, falls back to get_filter_options().
    Accepts string lists, model instances, and QuerySets.
    """
    if not areas and not locations and not sub_areas:
        return get_filter_options()

    from .models import Area, Location, SubArea

    if areas:
        if hasattr(areas, "values_list"):
            areas = list(areas.values_list("name", flat=True))
        elif not isinstance(areas, (list, tuple)):
            areas = [areas]
        areas = [str(a).lower() for a in areas]

    if locations:
        if hasattr(locations, "values_list"):
            locations = list(locations.values_list("name", flat=True))
        elif not isinstance(locations, (list, tuple)):
            locations = [locations]
        locations = [str(l).lower() for l in locations]

    if sub_areas:
        if hasattr(sub_areas, "values_list"):
            sub_areas = list(sub_areas.values_list("name", flat=True))
        elif not isinstance(sub_areas, (list, tuple)):
            sub_areas = [sub_areas]
        sub_areas = [str(s).lower() for s in sub_areas]

    area_key = ",".join(sorted(areas)) if areas else ""
    loc_key = ",".join(sorted(locations)) if locations else ""
    sub_key = ",".join(sorted(sub_areas)) if sub_areas else ""

    version = cache.get(COUNT_VERSION_KEY, 0)
    raw_key = f"{version}|{area_key}|{loc_key}|{sub_key}"
    cache_key = f"companies:available-filters:v1:{sha1(raw_key.encode()).hexdigest()}"

    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    available_areas_qs = Area.objects.all()
    if locations:
        available_areas_qs = available_areas_qs.filter(
            companies__location__name__in=locations
        )
    if sub_areas:
        available_areas_qs = available_areas_qs.filter(
            companies__sub_area__name__in=sub_areas
        )

    available_locations_qs = Location.objects.all()
    if areas:
        available_locations_qs = available_locations_qs.filter(
            companies__area__name__in=areas
        )
    if sub_areas:
        available_locations_qs = available_locations_qs.filter(
            companies__sub_area__name__in=sub_areas
        )

    available_sub_areas_qs = SubArea.objects.all()
    if areas:
        available_sub_areas_qs = available_sub_areas_qs.filter(
            companies__area__name__in=areas
        )
    if locations:
        available_sub_areas_qs = available_sub_areas_qs.filter(
            companies__location__name__in=locations
        )

    result = {
        "areas": list(
            available_areas_qs.values_list("name", flat=True)
            .distinct()
            .order_by("name")
        ),
        "locations": list(
            available_locations_qs.values_list("name", flat=True)
            .distinct()
            .order_by("name")
        ),
        "sub_areas": list(
            available_sub_areas_qs.values_list("name", flat=True)
            .distinct()
            .order_by("name")
        ),
    }

    cache.set(cache_key, result, AVAILABLE_FILTERS_TTL)
    return result


def bust_filter_caches():
    """Invalidate the options list cache and orphan all count/available-filters caches via version bump."""
    cache.delete(OPTIONS_CACHE_KEY)
    version = cache.get(COUNT_VERSION_KEY, 0)
    cache.set(COUNT_VERSION_KEY, version + 1, timeout=None)
