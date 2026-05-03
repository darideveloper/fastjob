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


@pytest.mark.django_db
def test_healthz_warns_when_google_oauth_in_testing_mode(client, settings, caplog):
    """A "Testing"-mode Google project still reports overall ok=200, but emits
    a warning in both the response body AND the log stream so operators see it
    on every probe.
    """
    import logging as _logging
    settings.GOOGLE_OAUTH_PROJECT_MODE = "testing"
    caplog.set_level(_logging.WARNING, logger="config.health")

    response = client.get("/healthz")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert any(
        "GOOGLE_OAUTH_PROJECT_MODE" in w for w in payload["warnings"]
    ), payload["warnings"]
    # Spec scenario also requires a structured log line.
    log_messages = "\n".join(r.getMessage() for r in caplog.records)
    assert "oauth_config_warning" in log_messages
    assert "GOOGLE_OAUTH_PROJECT_MODE" in log_messages


@pytest.mark.django_db
def test_healthz_no_warnings_in_production_mode(client, settings):
    settings.GOOGLE_OAUTH_PROJECT_MODE = "production"
    response = client.get("/healthz")
    payload = response.json()
    assert payload["warnings"] == []
