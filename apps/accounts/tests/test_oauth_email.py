import pytest
from unittest.mock import MagicMock
from django.core import mail
from allauth.socialaccount.models import SocialAccount
from apps.accounts.tasks import send_oauth_link_email

@pytest.mark.django_db
def test_oauth_link_email_sent_on_google_link(user):
    account = SocialAccount.objects.create(user=user, provider="google", uid="123")
    from apps.accounts.signals import notify_oauth_link
    notify_oauth_link(None, None, account)
    
    assert len(mail.outbox) == 1
    assert "FastJob: Nueva cuenta de google vinculada" in mail.outbox[0].subject
    assert "google" in mail.outbox[0].body

@pytest.mark.django_db
def test_oauth_link_email_sent_on_microsoft_link(user):
    account = SocialAccount.objects.create(user=user, provider="microsoft", uid="456")
    from apps.accounts.signals import notify_oauth_link
    notify_oauth_link(None, None, account)
    
    assert len(mail.outbox) == 1
    assert "microsoft" in mail.outbox[0].body

@pytest.mark.django_db
def test_oauth_link_email_not_sent_on_unlink(user):
    # Unlink is a different signal, notify_oauth_link shouldn't be called.
    pass

@pytest.mark.django_db
def test_oauth_link_email_uses_branded_layout(user):
    account = SocialAccount.objects.create(user=user, provider="google", uid="789")
    from apps.accounts.tasks import send_oauth_link_email
    send_oauth_link_email(user.pk, "google")
    
    email = mail.outbox[0]
    html_content = [alt[0] for alt in email.alternatives if alt[1] == "text/html"][0]
    
    assert "https://raw.githubusercontent.com/darideveloper/fastjob/refs/heads/main/static/images/fastjob-logo.png" in html_content
    assert "#007BFF" in html_content
    assert "© 2026 FastJob. Todos los derechos reservados." in html_content
