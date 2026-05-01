"""Tests for update_filters view — whitelist validation of area and location."""
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
def test_update_filters_valid_area_saves(client, user_with_cv):
    Company.objects.create(email="hr@a.com", name="A", area="Tecnología", location="Madrid")
    client.force_login(user_with_cv)
    resp = client.post(reverse("update_filters"), {"area_filter": "Tecnología", "location_filter": ""})
    assert resp.status_code == 302
    user_with_cv.refresh_from_db()
    assert user_with_cv.area_filter == "Tecnología"


@pytest.mark.django_db
def test_update_filters_invalid_area_rejected(client, user_with_cv):
    Company.objects.create(email="hr@a.com", name="A", area="Tecnología", location="")
    client.force_login(user_with_cv)
    resp = client.post(reverse("update_filters"), {"area_filter": "Bricolaje", "location_filter": ""})
    assert resp.status_code == 302
    user_with_cv.refresh_from_db()
    assert user_with_cv.area_filter == ""


@pytest.mark.django_db
def test_update_filters_invalid_area_shows_error(client, user_with_cv):
    Company.objects.create(email="hr@a.com", name="A", area="Tecnología", location="")
    client.force_login(user_with_cv)
    client.post(reverse("update_filters"), {"area_filter": "Fantasía", "location_filter": ""})
    resp = client.get(reverse("dashboard"))
    assert "no válido" in resp.content.decode()


@pytest.mark.django_db
def test_update_filters_empty_string_clears_filter(client, user_with_cv):
    user_with_cv.area_filter = "Tecnología"
    user_with_cv.save(update_fields=["area_filter"])
    Company.objects.create(email="hr@a.com", name="A", area="Tecnología", location="")
    client.force_login(user_with_cv)
    resp = client.post(reverse("update_filters"), {"area_filter": "", "location_filter": ""})
    assert resp.status_code == 302
    user_with_cv.refresh_from_db()
    assert user_with_cv.area_filter == ""


@pytest.mark.django_db
def test_update_filters_invalid_location_rejected(client, user_with_cv):
    Company.objects.create(email="hr@a.com", name="A", area="", location="Madrid")
    client.force_login(user_with_cv)
    resp = client.post(reverse("update_filters"), {"area_filter": "", "location_filter": "Marte"})
    assert resp.status_code == 302
    user_with_cv.refresh_from_db()
    assert user_with_cv.location_filter == ""
