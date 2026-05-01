"""Tests for the public company filter API endpoints."""
import json

import pytest
from django.core.cache import cache
from django.urls import reverse

from apps.companies.models import Company


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
    Company.objects.create(email="hr@acme.com", name="Acme", area="Tecnología", location="Madrid")
    resp = client.get(reverse("company_filter_options"))
    data = resp.json()
    keys = set(data.keys())
    assert keys == {"areas", "locations"}
    for forbidden in ("email", "name", "id", "pk"):
        assert forbidden not in keys


@pytest.mark.django_db
def test_filter_options_returns_distinct_sorted_values(client):
    Company.objects.create(email="a@x.com", name="A", area="Tecnología", location="Madrid")
    Company.objects.create(email="b@x.com", name="B", area="Diseño", location="Barcelona")
    resp = client.get(reverse("company_filter_options"))
    data = resp.json()
    assert "Tecnología" in data["areas"]
    assert "Diseño" in data["areas"]
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
    Company.objects.create(email="a@x.com", name="A", area="Tecnología", location="Madrid")
    Company.objects.create(email="b@x.com", name="B", area="Diseño", location="Barcelona")
    resp = client.get(reverse("company_count"))
    assert resp.json()["count"] == 2


@pytest.mark.django_db
def test_company_count_with_valid_area_uses_iexact(client):
    Company.objects.create(email="a@x.com", name="A", area="Tecnología", location="")
    Company.objects.create(email="b@x.com", name="B", area="Tecnología Industrial", location="")
    resp = client.get(reverse("company_count") + "?area=Tecnología")
    assert resp.json()["count"] == 1


@pytest.mark.django_db
def test_company_count_invalid_area_returns_400(client):
    Company.objects.create(email="a@x.com", name="A", area="Tecnología", location="")
    resp = client.get(reverse("company_count") + "?area=Bricolaje")
    assert resp.status_code == 400
    assert resp.json() == {"error": "invalid_filter"}


@pytest.mark.django_db
def test_company_count_invalid_location_returns_400(client):
    Company.objects.create(email="a@x.com", name="A", area="", location="Madrid")
    resp = client.get(reverse("company_count") + "?location=Marte")
    assert resp.status_code == 400
    assert resp.json() == {"error": "invalid_filter"}


@pytest.mark.django_db
def test_company_count_empty_param_means_no_filter(client):
    Company.objects.create(email="a@x.com", name="A", area="Tecnología", location="Madrid")
    Company.objects.create(email="b@x.com", name="B", area="Diseño", location="Madrid")
    resp = client.get(reverse("company_count") + "?area=&location=Madrid")
    assert resp.json()["count"] == 2


@pytest.mark.django_db
def test_company_count_response_contains_only_count_key(client):
    resp = client.get(reverse("company_count"))
    keys = set(resp.json().keys())
    assert keys == {"count"}


@pytest.mark.django_db
def test_company_count_error_response_contains_only_error_key(client):
    Company.objects.create(email="a@x.com", name="A", area="Tecnología", location="")
    resp = client.get(reverse("company_count") + "?area=Fake")
    keys = set(resp.json().keys())
    assert keys == {"error"}
    for forbidden in ("email", "name", "id", "pk"):
        assert forbidden not in keys
