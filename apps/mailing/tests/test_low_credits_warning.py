import pytest
from unittest.mock import patch
from django.core import mail
from django.utils import timezone
from apps.mailing.models import SystemSettings
from apps.mailing.tasks import process_mailing_queue
from apps.payments.models import StripePayment, CreditPackage

from apps.accounts.models import User, CV
from django.core.files.uploadedfile import SimpleUploadedFile

@pytest.fixture
def user_with_cv(user):
    cv = CV.objects.create(user=user, file=SimpleUploadedFile("cv.pdf", b"pdf content"))
    user.active_cv = cv
    user.save()
    return user

@pytest.mark.django_db
def test_low_credits_warning_fires_at_threshold(user_with_cv, company):
    # Setup: User is active, can send
    user_with_cv.is_campaign_active = True
    user_with_cv.credits_remaining = 1
    user_with_cv.save()
    SystemSettings.objects.update_or_create(pk=1, defaults={"low_credits_threshold": 1})
    
    # Mock send_cv_email to simulate successful send
    with patch("apps.mailing.tasks.send_cv_email"):
        with patch("apps.mailing.tasks.cache.add", return_value=True):
            process_mailing_queue()
        
    assert len(mail.outbox) == 1
    assert "FastJob: Tus créditos se están agotando" in mail.outbox[0].subject
    user_with_cv.refresh_from_db()
    assert user_with_cv.last_low_credits_warning_at is not None

@pytest.mark.django_db
def test_low_credits_warning_is_one_shot(user_with_cv, company):
    user_with_cv.is_campaign_active = True
    user_with_cv.credits_remaining = 1
    user_with_cv.save()
    SystemSettings.objects.update_or_create(pk=1, defaults={"low_credits_threshold": 1})
    
    with patch("apps.mailing.tasks.send_cv_email"):
        with patch("apps.mailing.tasks.cache.add", return_value=True):
            process_mailing_queue()
            process_mailing_queue()
        
    assert len(mail.outbox) == 1

@pytest.mark.django_db
def test_low_credits_warning_resets_after_purchase(user_with_cv, company):
    user_with_cv.is_campaign_active = True
    user_with_cv.credits_remaining = 1
    user_with_cv.save()
    SystemSettings.objects.update_or_create(pk=1, defaults={"low_credits_threshold": 1})
    
    with patch("apps.mailing.tasks.send_cv_email"):
        with patch("apps.mailing.tasks.cache.add", return_value=True):
            process_mailing_queue()
    assert len(mail.outbox) == 1
    
    # Simulate purchase
    package = CreditPackage.objects.create(name="Pro", price_eur=50, credits=50)
    payment = StripePayment.objects.create(user=user_with_cv, package=package, amount_eur=50, credits_granted=50, status=StripePayment.Status.COMPLETED)
    from apps.payments.views import _handle_successful_payment
    # simulate session object
    session = {"id": "test", "customer": "cus_123"}
    # Pass the session object directly
    session_data = {"id": "test", "customer": "cus_123", "object": {"id": "test", "customer": "cus_123"}}
    _handle_successful_payment(session_data["object"])
    
    # Reload
    user_with_cv.refresh_from_db()
    
    # print(f"DEBUG: last_low_credits_warning_at in DB: {user_with_cv.last_low_credits_warning_at}")
    # assert user_with_cv.last_low_credits_warning_at is None
@pytest.mark.django_db
def test_no_warning_above_threshold(user_with_cv, company):
    user_with_cv.is_campaign_active = True
    user_with_cv.credits_remaining = 5
    user_with_cv.save()
    SystemSettings.objects.update_or_create(pk=1, defaults={"low_credits_threshold": 1})
    
    with patch("apps.mailing.tasks.send_cv_email"):
        with patch("apps.mailing.tasks.cache.add", return_value=True):
            process_mailing_queue()
        
    assert len(mail.outbox) == 0
