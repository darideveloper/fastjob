import pytest
from django.core import mail
from apps.mailing.tasks import send_campaign_paused_notification

@pytest.mark.django_db
def test_paused_notification_has_html_alternative(user_with_cv):
    send_campaign_paused_notification(user_with_cv.pk, "quota")
    
    assert len(mail.outbox) == 1
    email = mail.outbox[0]
    
    # Check for text/html alternative
    has_html = False
    for alt in email.alternatives:
        if alt[1] == "text/html":
            has_html = True
            assert "logo" in alt[0]
            assert "FastJob" in alt[0]
            break
    assert has_html, "Email should have a text/html alternative"

@pytest.mark.django_db
def test_paused_notification_reasons_covered(user_with_cv):
    reasons = ["quota", "expired", "unlinked", "missing_cv", "other"]
    for reason in reasons:
        mail.outbox = []
        send_campaign_paused_notification(user_with_cv.pk, reason)
        assert len(mail.outbox) == 1
        assert "FastJob: Tu campaña ha sido pausada" in mail.outbox[0].subject

@pytest.mark.django_db
def test_paused_notification_uses_branded_layout(user_with_cv):
    send_campaign_paused_notification(user_with_cv.pk, "quota")
    
    email = mail.outbox[0]
    html_content = [alt[0] for alt in email.alternatives if alt[1] == "text/html"][0]
    
    # Check for branded elements in the rendered email
    assert "https://raw.githubusercontent.com/darideveloper/fastjob/refs/heads/main/static/images/fastjob-logo.png" in html_content
    assert "#007BFF" in html_content
    assert "© 2026 FastJob. Todos los derechos reservados." in html_content
