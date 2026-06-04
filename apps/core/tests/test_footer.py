import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_footer_contact_link(client):
    """
    Verify that the footer contains the correct mailto link for 'Contacto'.
    """
    url = reverse("home")
    response = client.get(url)
    
    assert response.status_code == 200
    # Check for the mailto link
    assert b'href="mailto:admin@fastjob.es"' in response.content
    assert b'Contacto' in response.content

@pytest.mark.django_db
def test_footer_legal_links(client):
    """
    Verify that the footer contains functional links to Privacy and Terms.
    """
    url = reverse("home")
    response = client.get(url)
    
    assert response.status_code == 200
    
    privacy_url = reverse("privacy")
    terms_url = reverse("terms")
    
    assert f'href="{privacy_url}"'.encode() in response.content
    assert f'href="{terms_url}"'.encode() in response.content

@pytest.mark.django_db
def test_footer_instagram_link(client):
    """
    Verify that the footer contains the correct Instagram link.
    """
    url = reverse("home")
    response = client.get(url)
    
    assert response.status_code == 200
    # Check for the official Instagram link
    assert b'href="https://www.instagram.com/fastjob.es"' in response.content
    assert b'aria-label="FastJob en Instagram"' in response.content
    assert b'target="_blank"' in response.content
    assert b'rel="noopener"' in response.content
