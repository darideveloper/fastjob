import pytest
from django.test import override_settings
from django.urls import path


from django.http import HttpResponse

def error_view(request):
    raise Exception("Test exception")


def dummy_view(request):
    return HttpResponse()


urlpatterns = [
    path("error/", error_view),
    path("privacidad/", dummy_view, name="privacy"),
    path("terminos/", dummy_view, name="terms"),
]

# Register the handler in the test module so it's picked up by ROOT_URLCONF
handler404 = "config.error_handlers.handler404"
handler500 = "config.error_handlers.handler500"


@pytest.mark.django_db
@override_settings(DEBUG=False, ROOT_URLCONF=__name__)
def test_handler404_browser(client):
    """Browser request to nonexistent URL returns HTML 404."""
    response = client.get("/nonexistent-url/")
    assert response.status_code == 404
    assert "text/html" in response["Content-Type"]
    # Verify it uses the template
    assert "Página no encontrada" in response.content.decode()


@pytest.mark.django_db
@override_settings(DEBUG=False, ROOT_URLCONF=__name__)
def test_handler404_xhr(client):
    """XHR request to nonexistent URL returns JSON 404."""
    response = client.get(
        "/nonexistent-url/", HTTP_X_REQUESTED_WITH="XMLHttpRequest"
    )
    assert response.status_code == 404
    assert "application/json" in response["Content-Type"]
    assert response.json() == {"error": "El recurso solicitado no existe."}


@pytest.mark.django_db
@override_settings(DEBUG=False, ROOT_URLCONF=__name__)
def test_handler500_browser(client):
    """Browser request that raises an exception returns HTML 500."""
    client.raise_request_exception = False
    response = client.get("/error/")
    assert response.status_code == 500
    assert "text/html" in response["Content-Type"]
    assert "Error del servidor" in response.content.decode()


@pytest.mark.django_db
@override_settings(DEBUG=False, ROOT_URLCONF=__name__)
def test_handler500_xhr(client):
    """XHR request that raises an exception returns JSON 500."""
    client.raise_request_exception = False
    response = client.get("/error/", HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    assert response.status_code == 500
    assert "application/json" in response["Content-Type"]
    assert response.json() == {"error": "Error interno del servidor."}
