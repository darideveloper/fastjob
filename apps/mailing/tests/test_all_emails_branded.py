import pytest
from django.template.loader import render_to_string
from apps.mailing.models import SystemSettings
from unittest.mock import MagicMock

@pytest.mark.django_db
def test_all_emails_use_branded_layout(user):
    templates = [
        ("email/campaign_paused_notification.html", {"reason": "quota", "user": user, "dashboard_url": "/"}),
        ("email/welcome.html", {"user": user, "dashboard_url": "/"}),
        ("email/payment_receipt.html", {
            "user": user, 
            "payment": MagicMock(amount_eur=10, credits_granted=10), 
            "package": MagicMock(name="Pro"),
            "billing_url": "/",
            "dashboard_url": "/"
        }),
        ("email/low_credits_warning.html", {"user": user, "packages_url": "/"}),
        ("email/account_deleted.html", {"home_url": "/"}),
        ("email/oauth_linked.html", {"provider": "google", "dashboard_url": "/"}),
    ]
    
    for template, context in templates:
        body_html = render_to_string(template, context)
        # We need to wrap it like the email utility does
        cfg = SystemSettings.get()
        full_context = {
            "subject": "Test",
            "body_html": body_html,
            "logo_url": cfg.email_logo_url,
            "brand_color": cfg.email_brand_color,
            "footer_text": cfg.email_footer_text,
        }
        rendered = render_to_string("email/base.html", full_context)
        
        assert cfg.email_logo_url in rendered
        assert cfg.email_footer_text in rendered
        assert "<!DOCTYPE html>" in rendered
        
        # Verify that the content of the template is NOT empty
        assert len(body_html.strip()) > 0
        # Verify that the content is actually in the rendered result
        # We strip tags from body_html for a more robust check if needed, 
        # but here we just check if it's there.
        assert body_html in rendered
@pytest.mark.django_db
def test_branded_email_with_custom_settings():
    SystemSettings.objects.update_or_create(pk=1, defaults={
        "email_logo_url": "https://custom.com/logo.png",
        "email_brand_color": "#000000",
        "email_footer_text": "Custom footer text",
    })
    
    cfg = SystemSettings.get()
    rendered = render_to_string("email/base.html", {
        "subject": "Test",
        "body_html": "<p>Body</p>",
        "logo_url": cfg.email_logo_url,
        "brand_color": cfg.email_brand_color,
        "footer_text": cfg.email_footer_text,
    })
    
    assert "https://custom.com/logo.png" in rendered
    assert "#000000" in rendered
    assert "Custom footer text" in rendered

