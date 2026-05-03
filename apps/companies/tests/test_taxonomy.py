import pytest
from django.db import IntegrityError
from apps.companies.models import Area, Location, Company

@pytest.mark.django_db
class TestTaxonomyModels:
    def test_area_creation(self):
        area = Area.objects.create(name="Software")
        assert str(area) == "Software"
        assert Area.objects.count() == 1

    def test_area_unique_constraint(self):
        Area.objects.create(name="Software")
        with pytest.raises(IntegrityError):
            Area.objects.create(name="Software")

    def test_location_creation(self):
        loc = Location.objects.create(name="Madrid")
        assert str(loc) == "Madrid"
        assert Location.objects.count() == 1

    def test_location_unique_constraint(self):
        Location.objects.create(name="Madrid")
        with pytest.raises(IntegrityError):
            Location.objects.create(name="Madrid")

    def test_company_fk_deletion_set_null(self):
        area = Area.objects.create(name="Software")
        company = Company.objects.create(
            email="test@example.com",
            name="Test Co",
            area=area
        )
        assert company.area == area
        
        area.delete()
        company.refresh_from_db()
        assert company.area is None

    def test_area_ordering(self):
        Area.objects.create(name="Z")
        Area.objects.create(name="A")
        areas = list(Area.objects.values_list("name", flat=True))
        assert areas == ["A", "Z"]
