import pytest
from django.urls import reverse
from apps.accounts.models import User

@pytest.mark.django_db
def test_user_model_visible_credits_clamping():
    user = User(credits_remaining=-5)
    assert user.visible_credits == 0
    
    user.credits_remaining = 10
    assert user.visible_credits == 10

@pytest.mark.django_db
def test_dashboard_ui_shows_zero_for_negative_balance(client, user):
    user.credits_remaining = -1337
    user.save()
    
    client.force_login(user)
    response = client.get(reverse("dashboard"))
    
    assert response.status_code == 200
    # The stat card value
    assert b"Env\xc3\xados disponibles" in response.content
    # Check that -1337 is NOT in the content, but 0 IS.
    # We look for the specific pattern from the template
    if b"-1337" in response.content:
        print(response.content.decode())
    assert b'<p class="text-3xl font-extrabold text-brand mb-2">0</p>' in response.content
    assert b"-1337" not in response.content

@pytest.mark.django_db
def test_navbar_shows_zero_for_negative_balance(client, user):
    user.credits_remaining = -3
    user.save()
    
    client.force_login(user)
    response = client.get(reverse("dashboard"))
    
    # Navbar chip: "{{ user.visible_credits }} envíos"
    assert b"0 env\xc3\xados" in response.content.lower()
