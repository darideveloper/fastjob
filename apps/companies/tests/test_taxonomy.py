import pytest
from django.db import IntegrityError
from apps.companies.models import Area, Location, Company

@pytest.mark.django_db
class TestTaxonomyModels:
    def test_area_creation(self):
        area = Area.objects.create(name="Software")
        assert str(area) == "software"
        assert Area.objects.count() == 1

    def test_area_unique_constraint(self):
        Area.objects.create(name="software")
        with pytest.raises(IntegrityError):
            Area.objects.create(name="software")

    def test_location_creation(self):
        loc = Location.objects.create(name="Madrid")
        assert str(loc) == "madrid"
        assert Location.objects.count() == 1

    def test_location_unique_constraint(self):
        Location.objects.create(name="madrid")
        with pytest.raises(IntegrityError):
            Location.objects.create(name="madrid")

    def test_company_fk_deletion_set_null(self):
        area = Area.objects.create(name="software")
        company = Company.objects.create(
            email="test@example.com",
            name="test co",
            area=area
        )
        assert company.area == area
        
        area.delete()
        company.refresh_from_db()
        assert company.area is None

    def test_area_ordering(self):
        Area.objects.create(name="z")
        Area.objects.create(name="a")
        areas = list(Area.objects.values_list("name", flat=True))
        assert areas == ["a", "z"]
