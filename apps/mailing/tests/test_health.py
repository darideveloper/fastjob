"""Tests for the /healthz endpoint."""
import pytest


@pytest.mark.django_db
def test_healthz_happy_path(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["db"] is True
    assert payload["cache"] is True


@pytest.mark.django_db
def test_healthz_degrades_when_db_fails(client, mocker):
    mocker.patch("config.health.connection.cursor", side_effect=Exception("db down"))
    response = client.get("/healthz")
    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "degraded"
    assert payload["db"] is False


@pytest.mark.django_db
def test_healthz_degrades_when_cache_fails(client, mocker):
    mocker.patch("config.health.cache.set", side_effect=Exception("redis down"))
    response = client.get("/healthz")
    assert response.status_code == 503
    payload = response.json()
    assert payload["cache"] is False
