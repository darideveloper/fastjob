import pytest
from unittest.mock import patch, MagicMock
from django.core import mail
from apps.accounts.models import User
from apps.accounts.tasks import send_welcome_email

@pytest.mark.django_db
def test_welcome_email_sent_on_signup():
    user = User.objects.create_user(email="test@example.com", username="test", first_name="Test")
    user.credits_remaining = 0
    user.save()
    
    # Simulate signal
    from apps.accounts.signals import grant_signup_bonus
    grant_signup_bonus(None, None, user)
    
    assert len(mail.outbox) == 1
    assert "Bienvenido a FastJob" in mail.outbox[0].subject
    assert "Test" in mail.outbox[0].body

@pytest.mark.django_db
def test_welcome_email_mentions_credits():
    user = User.objects.create_user(email="test@example.com", username="test1", credits_remaining=5)
    send_welcome_email(user.pk)
    
    assert "5" in mail.outbox[0].body

@pytest.mark.django_db
def test_welcome_email_failures_logged(caplog):
    user = User.objects.create_user(email="test@example.com", username="test2")
    with patch("apps.accounts.tasks.EmailMultiAlternatives.send", side_effect=Exception("Failed")):
        send_welcome_email(user.pk)
    
    assert "Failed to send welcome email" in caplog.text

@pytest.mark.django_db
def test_welcome_email_uses_first_name_or_email():
    user = User.objects.create_user(email="test@example.com", username="test3")
    send_welcome_email(user.pk)
    assert "test@example.com" in mail.outbox[0].body
    
    mail.outbox = []
    user.first_name = "Jane"
    user.save()
    send_welcome_email(user.pk)
    assert "Jane" in mail.outbox[0].body
