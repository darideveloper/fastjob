import pytest
from unittest.mock import patch
from django.core import mail
from django.urls import reverse
from apps.accounts.models import User

@pytest.mark.django_db
def test_deletion_email_sent_before_user_removed(client, user):
    client.force_login(user)
    
    response = client.post(reverse("delete_account"), {"confirm_email": user.email})
    assert response.status_code == 302
    
    assert len(mail.outbox) >= 1
    assert "FastJob: Tu cuenta ha sido eliminada" in mail.outbox[0].subject
    assert not User.objects.filter(pk=user.pk).exists()

@pytest.mark.django_db
def test_deletion_email_uses_branded_layout(client, user):
    client.force_login(user)
    
    client.post(reverse("delete_account"), {"confirm_email": user.email})
    
    assert len(mail.outbox) >= 1
    email = mail.outbox[0]
    html_content = [alt[0] for alt in email.alternatives if alt[1] == "text/html"][0]
    
    assert "https://raw.githubusercontent.com/darideveloper/fastjob/refs/heads/main/static/images/fastjob-logo.png" in html_content
    assert "#007BFF" in html_content
    assert "© 2026 FastJob. Todos los derechos reservados." in html_content

@pytest.mark.django_db
def test_deletion_continues_on_email_failure(client, user):
    client.force_login(user)
    
    with patch("apps.accounts.tasks.EmailMultiAlternatives.send", side_effect=Exception("Email failed")):
        response = client.post(reverse("delete_account"), {"confirm_email": user.email})
        assert response.status_code == 302
        
    assert not User.objects.filter(pk=user.pk).exists()
