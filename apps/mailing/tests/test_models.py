import datetime

import pytest
from django.core.exceptions import ValidationError
from apps.mailing.models import MailingLog, SystemSettings
from apps.accounts.models import User
from apps.companies.models import Company, Area, Location

@pytest.mark.django_db
def test_mailing_log_normalizes_email_snapshot():
    user = User.objects.create(email="user@example.com", username="user")
    log = MailingLog.objects.create(
        user=user,
        company_email_snapshot="MixedCase@Example.Com"
    )
    assert log.company_email_snapshot == "mixedcase@example.com"

@pytest.mark.django_db
def test_mailing_log_normalizes_on_update():
    user = User.objects.create(email="user@example.com", username="user")
    log = MailingLog.objects.create(
        user=user,
        company_email_snapshot="old@example.com"
    )
    log.company_email_snapshot = "New@Example.COM"
    log.save()
    assert log.company_email_snapshot == "new@example.com"

@pytest.mark.django_db
def test_mailing_log_clean_raises_on_empty_company_and_snapshot():
    user = User.objects.create(email="user@example.com", username="user")
    log = MailingLog(user=user)
    with pytest.raises(ValidationError, match="Debe proporcionarse una empresa o un snapshot del email."):
        log.full_clean()


# --- SystemSettings footer href scheme validation ---

def _settings(footer):
    cfg = SystemSettings()
    cfg.email_footer_text = footer
    cfg.email_sending_start_time = datetime.time(10, 0)
    cfg.email_sending_end_time = datetime.time(20, 0)
    return cfg


@pytest.mark.django_db
def test_footer_clean_accepts_https_link():
    cfg = _settings('<a href="https://example.com/terms">Terms</a>')
    cfg.full_clean()


@pytest.mark.django_db
def test_footer_clean_accepts_mailto_link():
    cfg = _settings('<a href="mailto:support@example.com">Contact</a>')
    cfg.full_clean()


@pytest.mark.django_db
def test_footer_clean_rejects_javascript_link():
    cfg = _settings('<a href="javascript:alert(1)">Click</a>')
    with pytest.raises(ValidationError, match="javascript:alert"):
        cfg.full_clean()


@pytest.mark.django_db
def test_footer_clean_rejects_relative_path():
    cfg = _settings('<a href="/terms">Terms</a>')
    with pytest.raises(ValidationError, match="/terms"):
        cfg.full_clean()


@pytest.mark.django_db
def test_footer_clean_error_includes_line_number():
    cfg = _settings('© 2026\n<a href="tel:+1234">Call</a>')
    with pytest.raises(ValidationError, match="línea 2"):
        cfg.full_clean()


@pytest.mark.django_db
def test_footer_clean_still_validates_send_time_equality():
    cfg = SystemSettings()
    cfg.email_footer_text = "plain text, no links"
    cfg.email_sending_start_time = datetime.time(10, 0)
    cfg.email_sending_end_time = datetime.time(10, 0)
    with pytest.raises(ValidationError, match="hora de fin"):
        cfg.full_clean()
