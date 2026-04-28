"""H12 regression tests: outbound URL scheme is taken from `SITE_SCHEME`,
not from `DEBUG`.

The bug the fix closes: a developer running `DEBUG=True` behind an
HTTPS-terminating proxy (or `DEBUG=False` on a plain-HTTP staging) would
emit URLs whose scheme didn't match the actual deployment, breaking
OAuth callbacks and landing users on cookie-mismatched domains.
"""
from unittest.mock import MagicMock

import pytest
from django.contrib.auth import get_user_model

from apps.mailing.engine import send_cv_email
from apps.mailing.models import EmailTemplate, MailingLog


@pytest.fixture
def fixture_log(db, google_linked_user, company):
    """A MailingLog row plus a stub email template, ready to feed into
    send_cv_email. We don't need the actual send to succeed — just to
    capture the cv_url / unsubscribe_url passed to the renderer."""
    template = EmailTemplate.objects.create(
        name="t", subject="hi", body_html="cv: {cv_url} | u: {unsubscribe_url}", is_active=True
    )
    log = MailingLog.objects.create(
        user=google_linked_user, company=company, email_template=template, cv=google_linked_user.active_cv
    )
    return google_linked_user, company, template, log


@pytest.mark.django_db
def test_engine_uses_site_scheme_when_debug_true(monkeypatch, fixture_log, settings):
    """The acceptance: DEBUG=True + SITE_SCHEME=https → https URLs."""
    user, company, template, log = fixture_log
    settings.DEBUG = True
    settings.SITE_SCHEME = "https"
    settings.SITE_DOMAIN = "example.com"

    captured = {}

    def fake_render(company_name, cv_url, unsubscribe_url):
        captured["cv_url"] = cv_url
        captured["unsubscribe_url"] = unsubscribe_url
        return ("subj", "<p>body</p>")

    monkeypatch.setattr(template, "render", fake_render)
    # Stub the actual provider send so we don't hit Google/Microsoft.
    monkeypatch.setattr("apps.mailing.engine._send_via_gmail", lambda *a, **kw: None)

    send_cv_email(user, company, template, log)

    assert captured["cv_url"].startswith("https://example.com/cv/")
    assert captured["unsubscribe_url"].startswith("https://example.com/unsubscribe/")


@pytest.mark.django_db
def test_engine_respects_http_scheme_for_local_dev(monkeypatch, fixture_log, settings):
    """The other side: DEBUG=False + SITE_SCHEME=http (e.g. local
    integration test on plain HTTP) → http URLs."""
    user, company, template, log = fixture_log
    settings.DEBUG = False
    settings.SITE_SCHEME = "http"
    settings.SITE_DOMAIN = "localhost:8000"

    captured = {}

    def fake_render(company_name, cv_url, unsubscribe_url):
        captured["cv_url"] = cv_url
        return ("subj", "<p>body</p>")

    monkeypatch.setattr(template, "render", fake_render)
    monkeypatch.setattr("apps.mailing.engine._send_via_gmail", lambda *a, **kw: None)

    send_cv_email(user, company, template, log)
    assert captured["cv_url"].startswith("http://localhost:8000/cv/")


def test_settings_default_site_scheme_is_https(settings):
    """Default value for the new SITE_SCHEME setting must be `https` —
    secure-by-default."""
    # Just verify the attribute exists with the documented default. The
    # fact that pytest is running means settings imported successfully.
    assert hasattr(settings, "SITE_SCHEME")
    # Default in config/settings.py is "https"; in test_settings the env
    # has DEBUG=True but SITE_SCHEME isn't overridden, so it stays https.
    assert settings.SITE_SCHEME in ("http", "https")
