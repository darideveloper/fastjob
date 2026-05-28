import pytest
from unittest.mock import patch, MagicMock
from apps.mailing.engine import send_cv_email
from apps.mailing.models import EmailTemplate

@pytest.mark.django_db
def test_cv_email_uses_branded_layout(user_with_cv, company):
    template = EmailTemplate.objects.create(name="Test", subject="Test", body_html="<h1>Test</h1>")
    
    with patch("apps.mailing.engine._send_via_gmail") as mock_gmail:
        # Mocking OAuth token refresh to avoid side effects
        with patch("apps.mailing.engine._get_social_token", return_value=("google", None, None)):
            with patch("apps.mailing.engine._refresh_google_token", return_value="token"):
                send_cv_email(user_with_cv, company, template, MagicMock())
    
    args, kwargs = mock_gmail.call_args
    body_html = args[4]
    
    assert "<h1>Test</h1>" in body_html
    assert "https://raw.githubusercontent.com/darideveloper/fastjob/refs/heads/main/static/images/fastjob-logo.png" in body_html
    assert "© 2026 FastJob. Todos los derechos reservados." in body_html
    assert "<!DOCTYPE html>" in body_html
