import pytest
from allauth.account.signals import user_signed_up
from apps.mailing.models import SystemSettings
from apps.accounts.models import User

@pytest.mark.django_db
def test_grant_signup_bonus_uses_dynamic_setting():
    # Set dynamic bonus to 10
    cfg = SystemSettings.get()
    cfg.initial_free_credits = 10
    cfg.save()

    # Create a user and trigger the signal
    user = User.objects.create_user(username="newuser", email="new@test.com", password="password")
    user_signed_up.send(sender=None, request=None, user=user)

    user.refresh_from_db()
    assert user.credits_remaining == 10

@pytest.mark.django_db
def test_grant_signup_bonus_defaults_to_five():
    # Ensure default is 5
    cfg = SystemSettings.get()
    assert cfg.initial_free_credits == 5

    user = User.objects.create_user(username="newuser2", email="new2@test.com", password="password")
    user_signed_up.send(sender=None, request=None, user=user)

    user.refresh_from_db()
    assert user.credits_remaining == 5
