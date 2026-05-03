## Context
The project currently uses `CharField` for `area` and `location` in `Company` and `User`. The dropdown options are generated via `DISTINCT` queries in `apps.companies.queries._get_distinct_values`.

## Architectural Changes

### 1. Database Schema
We will introduce two new models in `apps.companies.models`:

```python
class Area(models.Model):
    name = models.CharField(max_length=200, unique=True)
    def __str__(self): return self.name

class Location(models.Model):
    name = models.CharField(max_length=200, unique=True)
    def __str__(self): return self.name
```

The `Company` model will be updated:
- `area` -> `ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True)`
- `location` -> `ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)`

The `User` model will be updated:
- `area_filter` -> `ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True)`
- `location_filter` -> `ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)`

### 2. Migration Strategy
A multi-step migration is required:
1. **Schema Update (Add FKs)**: Add the new FK fields (e.g., `area_link`) while keeping the old `CharField` fields.
2. **Data Migration**: 
    - Extract distinct values from `Company.area` and `Company.location`.
    - Create `Area` and `Location` records.
    - Update `Company` and `User` FKs to point to the new records based on string matching.
3. **Schema Cleanup**: Remove the old `CharField` fields and rename the FK fields to the original names.

### 3. API & Security
- The `filter_options_view` will now query `Area.objects.all()` and `Location.objects.all()`.
- The `companies_count_view` will validate against these models.
- The `ratelimit` remains in place to prevent scraping.
- Selection will be restricted to IDs (or names, but IDs are safer for FK consistency).

### 4. Admin Integration
- `UserAdmin` will use standard Django `ForeignKey` widgets (Select) for `area_filter` and `location_filter`, ensuring staff can only pick valid options.
- The `XlsxImporter` will be updated to lookup or create `Area`/`Location` objects during import.

### 5. Layout Adjustments
- **Landing Hero**: Place the company counter inside the same container as the filters to create a unified "Search Bar" feel.
- **Dashboard**: Align the counter horizontally with the filters if space permits, otherwise keep it directly adjacent.

## Trade-offs
- **Complexity**: ForeignKeys add more overhead during joins and migrations compared to plain CharFields.
- **Data Rigidity**: Admins MUST create an Area/Location before it can be used in a Company or User filter. We can mitigate this by allowing the importer to create missing taxonomy entries automatically (optional).
