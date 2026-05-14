import pytest
from apps.mailing.models import SystemSettings, MailingLog
from apps.mailing.tasks import process_mailing_queue
from apps.accounts.models import User
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch

@pytest.mark.django_db
def test_mailing_engine_respects_hidden_multiplier(google_linked_user, company, email_template):
    with patch("apps.mailing.tasks.send_cv_email"):
        # Set hidden multiplier to 1.1 (10% extra)
        cfg = SystemSettings.get()
        cfg.hidden_credit_multiplier = 1.1
        cfg.save()

        # User has purchased 50 credits, used them all, now at 0
        google_linked_user.total_purchased_credits = 50
        google_linked_user.credits_remaining = 0
        google_linked_user.is_campaign_active = True
        google_linked_user.save()

        # Engine should send 5 more (floor is -5)
        for i in range(5):
            # Reset interval AND company cooldown constraints
            MailingLog.objects.filter(user=google_linked_user).update(sent_at=timezone.now() - timedelta(hours=24))
            
            process_mailing_queue()
            google_linked_user.refresh_from_db()
            assert google_linked_user.credits_remaining == -(i + 1)
            assert MailingLog.objects.filter(user=google_linked_user, status=MailingLog.Status.SENT).count() == i + 1
        
        # After 5 sends, balance is -5. Floor is -5. Next send should fail.
        process_mailing_queue()
        google_linked_user.refresh_from_db()
        assert google_linked_user.credits_remaining == -5
        assert MailingLog.objects.filter(user=google_linked_user, status=MailingLog.Status.SENT).count() == 5

@pytest.mark.django_db
def test_mailing_engine_skips_user_at_limit_no_multiplier(google_linked_user, company, email_template):
    # Multiplier 1.0 (default)
    google_linked_user.total_purchased_credits = 50
    google_linked_user.credits_remaining = 0
    google_linked_user.is_campaign_active = True
    google_linked_user.save()

    process_mailing_queue()
    google_linked_user.refresh_from_db()
    assert google_linked_user.credits_remaining == 0
    assert MailingLog.objects.filter(user=google_linked_user, status=MailingLog.Status.SENT).count() == 0
