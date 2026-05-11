from hashlib import sha1

from django.core.cache import cache

OPTIONS_CACHE_KEY = "companies:filter-options:v1"
COUNT_VERSION_KEY = "companies:count:version"
OPTIONS_TTL = 300  # 5 minutes
COUNT_TTL = 60  # 1 minute


def get_filter_options():
    """Return {"areas": [...], "locations": [...]} from Managed Taxonomy, cached 5 min."""
    from .models import Area, Location

    cached = cache.get(OPTIONS_CACHE_KEY)
    if cached is not None:
        return cached

    result = {
        "areas": list(Area.objects.values_list("name", flat=True).order_by("name")),
        "locations": list(Location.objects.values_list("name", flat=True).order_by("name")),
    }
    cache.set(OPTIONS_CACHE_KEY, result, OPTIONS_TTL)
    return result


def matching_companies_qs(areas=None, locations=None):
    """Return a Company QS filtered by area/location names.

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

    return qs


def get_company_count(areas=None, locations=None):
    """Count companies matching area/location filters, with 60 s cache."""
    # Ensure stable cache key by sorting inputs if they are lists
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

    version = cache.get(COUNT_VERSION_KEY, 0)
    raw_key = f"{version}|{area_key}|{loc_key}"
    cache_key = f"companies:count:v1:{sha1(raw_key.encode()).hexdigest()}"

    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    count = matching_companies_qs(areas, locations).count()
    cache.set(cache_key, count, COUNT_TTL)
    return count


def bust_filter_caches():
    """Invalidate the options list cache and orphan all count caches via version bump."""
    cache.delete(OPTIONS_CACHE_KEY)
    version = cache.get(COUNT_VERSION_KEY, 0)
    cache.set(COUNT_VERSION_KEY, version + 1, timeout=None)
