import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_microsoft_identity_association_view(client):
    url = reverse("microsoft_identity_association")
    response = client.get(url)

    assert response.status_code == 200
    assert response["Content-Type"] == "application/json"

    expected_data = {
        "associatedApplications": [
            {"applicationId": "3853b95b-027f-4c59-94e4-d697b2a603a9"}
        ]
    }
    assert response.json() == expected_data


@pytest.mark.django_db
def test_microsoft_identity_association_url(client):
    response = client.get("/.well-known/microsoft-identity-association.json")
    assert response.status_code == 200


@pytest.mark.django_db
def test_privacy_page_spanish(client):
    url = reverse("privacy")
    response = client.get(url)
    assert response.status_code == 200
    assert b"dpo@basquekide.es" in response.content
    assert b"No compartimos ni transferimos:" in response.content
    assert b"gmail.send" in response.content
    assert b"Mail.Send" in response.content
    assert b"cookie-banner" in response.content


@pytest.mark.django_db
def test_privacy_page_english(client):
    url = reverse("privacy_en")
    response = client.get(url)
    assert response.status_code == 200
    assert b"dpo@basquekide.es" in response.content
    assert b"No compartimos ni transferimos:" in response.content
    assert b"gmail.send" in response.content
    assert b"Mail.Send" in response.content
    assert b"cookie-banner" in response.content


@pytest.mark.django_db
def test_terms_page_spanish(client):
    url = reverse("terms")
    response = client.get(url)
    assert response.status_code == 200
    assert b"dpo@basquekide.es" in response.content
    assert b"open-cookie-settings" in response.content
    assert b"cookie-banner" in response.content


@pytest.mark.django_db
def test_terms_page_english(client):
    url = reverse("terms_en")
    response = client.get(url)
    assert response.status_code == 200
    assert b"dpo@basquekide.es" in response.content
    assert b"open-cookie-settings" in response.content
    assert b"cookie-banner" in response.content


