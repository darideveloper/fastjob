"""Tests for update_filters view — whitelist validation of area and location."""
import pytest
from django.core.cache import cache
from django.urls import reverse

from apps.companies.models import Company, Area, Location, SubArea


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
def test_update_filters_valid_area_saves(client, user_with_cv):
    a, _ = Area.objects.get_or_create(name="Tecnología")
    l, _ = Location.objects.get_or_create(name="Madrid")
    Company.objects.create(email="hr@a.com", name="A", area=a, location=l)
    client.force_login(user_with_cv)
    resp = client.post(reverse("update_filters"), {"area_filter": ["Tecnología"], "location_filter": []})
    assert resp.status_code == 302
    user_with_cv.refresh_from_db()
    assert user_with_cv.area_filters.filter(name="tecnología").exists()


@pytest.mark.django_db
def test_update_filters_multiple_areas_saves(client, user_with_cv):
    a1, _ = Area.objects.get_or_create(name="Tecnología")
    a2, _ = Area.objects.get_or_create(name="Diseño")
    Company.objects.create(email="hr@a.com", name="A", area=a1)
    Company.objects.create(email="hr@b.com", name="B", area=a2)
    client.force_login(user_with_cv)
    resp = client.post(reverse("update_filters"), {"area_filter": ["Tecnología", "Diseño"], "location_filter": []})
    assert resp.status_code == 302
    user_with_cv.refresh_from_db()
    assert user_with_cv.area_filters.count() == 2


@pytest.mark.django_db
def test_update_filters_invalid_area_rejected(client, user_with_cv):
    a, _ = Area.objects.get_or_create(name="Tecnología")
    Company.objects.create(email="hr@a.com", name="A", area=a, location=None)
    client.force_login(user_with_cv)
    resp = client.post(reverse("update_filters"), {"area_filter": ["Bricolaje"], "location_filter": []})
    assert resp.status_code == 302
    user_with_cv.refresh_from_db()
    assert user_with_cv.area_filters.count() == 0


@pytest.mark.django_db
def test_update_filters_invalid_area_shows_error(client, user_with_cv):
    a, _ = Area.objects.get_or_create(name="Tecnología")
    Company.objects.create(email="hr@a.com", name="A", area=a, location=None)
    client.force_login(user_with_cv)
    client.post(reverse("update_filters"), {"area_filter": ["Fantasía"], "location_filter": []})
    resp = client.get(reverse("dashboard"))
    assert "no válido" in resp.content.decode()


@pytest.mark.django_db
def test_update_filters_empty_string_clears_filter(client, user_with_cv):
    a, _ = Area.objects.get_or_create(name="Tecnología")
    user_with_cv.area_filters.add(a)
    Company.objects.create(email="hr@a.com", name="A", area=a, location=None)
    client.force_login(user_with_cv)
    resp = client.post(reverse("update_filters"), {"area_filter": [], "location_filter": []})
    assert resp.status_code == 302
    user_with_cv.refresh_from_db()
    assert user_with_cv.area_filters.count() == 0


@pytest.mark.django_db
def test_update_filters_invalid_location_rejected(client, user_with_cv):
    l, _ = Location.objects.get_or_create(name="Madrid")
    Company.objects.create(email="hr@a.com", name="A", area=None, location=l)
    client.force_login(user_with_cv)
    resp = client.post(reverse("update_filters"), {"area_filter": [], "location_filter": ["Marte"]})
    assert resp.status_code == 302
    user_with_cv.refresh_from_db()
    assert user_with_cv.location_filters.count() == 0


@pytest.mark.django_db
def test_update_filters_valid_sub_area_saves(client, user_with_cv):
    s, _ = SubArea.objects.get_or_create(name="limpieza")
    Company.objects.create(email="hr@a.com", name="A", sub_area=s)
    client.force_login(user_with_cv)
    resp = client.post(
        reverse("update_filters"),
        {"area_filter": [], "location_filter": [], "sub_area_filter": ["limpieza"]}
    )
    assert resp.status_code == 302
    user_with_cv.refresh_from_db()
    assert user_with_cv.sub_area_filters.filter(name="limpieza").exists()


@pytest.mark.django_db
def test_update_filters_invalid_sub_area_rejected(client, user_with_cv):
    s, _ = SubArea.objects.get_or_create(name="limpieza")
    Company.objects.create(email="hr@a.com", name="A", sub_area=s)
    client.force_login(user_with_cv)
    resp = client.post(
        reverse("update_filters"),
        {"area_filter": [], "location_filter": [], "sub_area_filter": ["invalidsubarea"]}
    )
    assert resp.status_code == 302
    user_with_cv.refresh_from_db()
    assert user_with_cv.sub_area_filters.count() == 0
