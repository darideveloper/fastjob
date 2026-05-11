## ADDED Requirements

### Requirement: Robust Company Filter Normalization
The `matching_companies_qs` helper MUST robustly handle both string inputs and model instances (or iterables of model instances) for the `area` and `location` filters. If passed model instances, it MUST extract their `.name` attribute before filtering the `Company` queryset.

#### Scenario: Helper accepts single model instances
- **GIVEN** an `Area` model instance with `name="Tecnología"`
- **WHEN** it is passed as the `area` argument to `matching_companies_qs`
- **THEN** the helper extracts the name and correctly filters `Company.objects.filter(area__name__iexact="Tecnología")`
- **AND** no `psycopg2.ProgrammingError` is raised.

#### Scenario: Helper accepts QuerySet of model instances
- **GIVEN** a `QuerySet` of `Area` model instances (e.g., from `user.area_filters.all()`)
- **WHEN** it is passed as the `area` argument
- **THEN** the helper extracts the names into a list and correctly filters using `area__name__in=[...]`