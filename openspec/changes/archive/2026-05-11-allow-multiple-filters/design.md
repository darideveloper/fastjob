# Multi-Select Filter Design

## Context
Currently, `User` has `area_filter` and `location_filter` defined as `ForeignKey`s to `companies.Area` and `companies.Location`. This allows a user to target only a single area and/or location for their campaign. The user wishes to expand this so a campaign can target multiple areas and multiple locations simultaneously.

## Data Model Changes
We must change `User.area_filter` and `User.location_filter` to `area_filters` and `location_filters` as `ManyToManyField`s.

```python
class User(AbstractUser):
    # ...
    area_filters = models.ManyToManyField("companies.Area", blank=True, related_name="users")
    location_filters = models.ManyToManyField("companies.Location", blank=True, related_name="users")
```

**Migration Strategy**:
1. Add `area_filters` and `location_filters` `ManyToManyField`s to `User`.
2. Data migration: For every `User` with a non-null `area_filter`, add it to `area_filters.add()`. Do the same for `location_filter`.
3. Remove `area_filter` and `location_filter` `ForeignKey`s from `User`.

## Query Changes
The `matching_companies_qs(areas=None, locations=None)` helper in `apps/companies/queries.py` currently accepts single strings or objects. We need to update it to accept lists of strings or QuerySets of Area/Location.

```python
def matching_companies_qs(areas=None, locations=None):
    qs = Company.objects.all()
    if areas:
        qs = qs.filter(area__name__in=[a.name for a in areas] if not isinstance(areas[0], str) else areas)
    if locations:
        qs = qs.filter(location__name__in=[l.name for l in locations] if not isinstance(locations[0], str) else locations)
    return qs
```

## Cache Invalidation
`get_company_count` generates a cache key based on the filter values. We must ensure the list is sorted and stringified consistently to hit the cache properly regardless of input order.

## Frontend UI
The `combobox.js` and `templates/dashboard/index.html` (and landing page) must be updated to support selecting multiple items. Selected items should appear as removable "pill" tags next to the input. The underlying form submission must send multiple values (e.g., `area_filters=Tecnología&area_filters=Diseño` or a comma-separated list/JSON payload) which the Django view will process using `request.POST.getlist("area_filters")`.

## Mailing Engine
`apps/mailing/tasks.py` needs to pass `user.area_filters.all()` and `user.location_filters.all()` to `matching_companies_qs`.
