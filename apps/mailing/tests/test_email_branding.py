from django.test import TestCase
from apps.mailing.models import SystemSettings
from apps.mailing.email import render_branded_email

class TestEmailBranding(TestCase):
    def test_email_branding_defaults(self):
        cfg = SystemSettings.get()
        rendered = render_branded_email("Test Subject", "<p>Hello</p>")
        self.assertIn("https://raw.githubusercontent.com/daridev/fastjob/main/static/images/fastjob-logo.png", rendered)
        self.assertIn("#007BFF", rendered)
        self.assertIn("© 2026 FastJob. Todos los derechos reservados.", rendered)
        self.assertIn("<p>Hello</p>", rendered)

    def test_email_branding_custom_values(self):
        SystemSettings.objects.update_or_create(pk=1, defaults={
            "email_logo_url": "https://example.com/logo.png",
            "email_brand_color": "#FF0000",
            "email_footer_text": "Custom Footer",
        })
        rendered = render_branded_email("Test Subject", "<p>Hello</p>")
        self.assertIn("https://example.com/logo.png", rendered)
        self.assertIn("#FF0000", rendered)
        self.assertIn("Custom Footer", rendered)

    def test_invalid_brand_color_rejected(self):
        cfg = SystemSettings.get()
        cfg.email_brand_color = "invalid"
        with self.assertRaises(Exception):
            cfg.full_clean()

    def test_negative_threshold_rejected(self):
        cfg = SystemSettings.get()
        cfg.low_credits_threshold = -1
        with self.assertRaises(Exception):
            cfg.full_clean()

    def test_render_branded_email_wraps_content(self):
        rendered = render_branded_email("Subject", "<h1>Body</h1>")
        self.assertIn("<h1>Body</h1>", rendered)
        self.assertIn("<!DOCTYPE html>", rendered)
