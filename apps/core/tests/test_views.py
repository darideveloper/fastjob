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
