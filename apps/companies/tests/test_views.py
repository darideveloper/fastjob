"""Tests for the public company filter API endpoints."""
import json

import pytest
from django.core.cache import cache
from django.urls import reverse

from apps.companies.models import Company, Area, Location


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
def test_filter_options_anonymous_returns_200(client):
    resp = client.get(reverse("company_filter_options"))
    assert resp.status_code == 200
    data = resp.json()
    assert "areas" in data
    assert "locations" in data


@pytest.mark.django_db
def test_filter_options_payload_contains_no_identifying_fields(client):
    a, _ = Area.objects.get_or_create(name="tecnología")
    l, _ = Location.objects.get_or_create(name="madrid")
    Company.objects.create(email="hr@acme.com", name="acme", area=a, location=l)
    resp = client.get(reverse("company_filter_options"))
    data = resp.json()
    keys = set(data.keys())
    assert keys == {"areas", "locations"}
    for forbidden in ("email", "name", "id", "pk"):
        assert forbidden not in keys


@pytest.mark.django_db
def test_filter_options_returns_distinct_sorted_values(client):
    a1, _ = Area.objects.get_or_create(name="tecnología")
    l1, _ = Location.objects.get_or_create(name="madrid")
    a2, _ = Area.objects.get_or_create(name="diseño")
    l2, _ = Location.objects.get_or_create(name="barcelona")
    Company.objects.create(email="a@x.com", name="a", area=a1, location=l1)
    Company.objects.create(email="b@x.com", name="b", area=a2, location=l2)
    resp = client.get(reverse("company_filter_options"))
    data = resp.json()
    assert "tecnología" in data["areas"]
    assert "diseño" in data["areas"]
    assert data["areas"] == sorted(data["areas"], key=str.lower)


@pytest.mark.django_db
def test_company_count_anonymous_returns_200(client):
    resp = client.get(reverse("company_count"))
    assert resp.status_code == 200
    data = resp.json()
    assert "count" in data
    assert isinstance(data["count"], int)


@pytest.mark.django_db
def test_company_count_no_params_equals_total(client):
    a1, _ = Area.objects.get_or_create(name="tecnología")
    l1, _ = Location.objects.get_or_create(name="madrid")
    a2, _ = Area.objects.get_or_create(name="diseño")
    l2, _ = Location.objects.get_or_create(name="barcelona")
    Company.objects.create(email="a@x.com", name="a", area=a1, location=l1)
    Company.objects.create(email="b@x.com", name="b", area=a2, location=l2)
    resp = client.get(reverse("company_count"))
    assert resp.json()["count"] == 2


@pytest.mark.django_db
def test_company_count_with_valid_area_uses_iexact(client):
    a1, _ = Area.objects.get_or_create(name="tecnología")
    a2, _ = Area.objects.get_or_create(name="tecnología industrial")
    Company.objects.create(email="a@x.com", name="a", area=a1)
    Company.objects.create(email="b@x.com", name="b", area=a2)
    resp = client.get(reverse("company_count") + "?area=tecnología")
    assert resp.json()["count"] == 1


@pytest.mark.django_db
def test_company_count_invalid_area_returns_400(client):
    a1, _ = Area.objects.get_or_create(name="tecnología")
    Company.objects.create(email="a@x.com", name="a", area=a1)
    # "bricolaje" doesn't exist in Area model
    resp = client.get(reverse("company_count") + "?area=bricolaje")
    assert resp.status_code == 400
    assert resp.json() == {"error": "invalid_filter"}


@pytest.mark.django_db
def test_company_count_invalid_location_returns_400(client):
    l1, _ = Location.objects.get_or_create(name="madrid")
    Company.objects.create(email="a@x.com", name="a", location=l1)
    # "marte" doesn't exist in Location model
    resp = client.get(reverse("company_count") + "?location=marte")
    assert resp.status_code == 400
    assert resp.json() == {"error": "invalid_filter"}


@pytest.mark.django_db
def test_company_count_empty_param_means_no_filter(client):
    a1, _ = Area.objects.get_or_create(name="tecnología")
    l1, _ = Location.objects.get_or_create(name="madrid")
    a2, _ = Area.objects.get_or_create(name="diseño")
    Company.objects.create(email="a@x.com", name="a", area=a1, location=l1)
    Company.objects.create(email="b@x.com", name="b", area=a2, location=l1)
    resp = client.get(reverse("company_count") + "?area=&location=madrid")
    assert resp.json()["count"] == 2


@pytest.mark.django_db
def test_company_count_response_contains_only_count_key(client):
    resp = client.get(reverse("company_count"))
    keys = set(resp.json().keys())
    assert keys == {"count"}


@pytest.mark.django_db
def test_company_count_error_response_contains_only_error_key(client):
    a1, _ = Area.objects.get_or_create(name="Tecnología")
    Company.objects.create(email="a@x.com", name="A", area=a1)
    resp = client.get(reverse("company_count") + "?area=Fake")
    keys = set(resp.json().keys())
    assert keys == {"error"}
    for forbidden in ("email", "name", "id", "pk"):
        assert forbidden not in keys
