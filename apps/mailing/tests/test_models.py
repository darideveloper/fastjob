import pytest
from django.core.exceptions import ValidationError
from apps.mailing.models import MailingLog
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
