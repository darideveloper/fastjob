import pytest
from apps.companies.models import Area, Location, Company

@pytest.mark.django_db
def test_area_name_is_lowercased():
    area = Area.objects.create(name="TECNOLOGÍA")
    assert area.name == "tecnología"
    
    area.name = "DISEÑO"
    area.save()
    assert area.name == "diseño"

@pytest.mark.django_db
def test_location_name_is_lowercased():
    loc = Location.objects.create(name="MADRID")
    assert loc.name == "madrid"

@pytest.mark.django_db
def test_company_fields_are_lowercased():
    company = Company.objects.create(
        email="HR@ACME.COM",
        name="ACME CORP",
        address="CALLE MAYOR, 1",
        province="MADRID",
        community="COM. MADRID",
        website="WWW.ACME.COM"
    )
    assert company.email == "hr@acme.com"
    assert company.name == "acme corp"
    assert company.address == "calle mayor, 1"
    assert company.province == "madrid"
    assert company.community == "com. madrid"
    assert company.website == "www.acme.com"

@pytest.mark.django_db
def test_company_zip_and_phone_not_lowercased():
    # These fields don't usually have letters, but let's be sure we don't break them if they do
    company = Company.objects.create(
        email="test@test.com",
        name="test",
        zip_code="ABC-123",
        phone="TEL: 123"
    )
    assert company.zip_code == "ABC-123"
    assert company.phone == "TEL: 123"
