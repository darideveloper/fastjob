
import pytest
from unittest.mock import patch
from apps.mailing.tasks import process_mailing_queue
from apps.mailing.engine import TokenExpiredError
from apps.mailing.models import MailingLog, SystemSettings
from django.core import mail

@pytest.fixture
def settings_obj(db):
    obj, _ = SystemSettings.objects.update_or_create(
        pk=1,
        defaults={
            "global_send_interval_minutes": 5,
            "company_cooldown_hours": 12,
            "max_emails_per_day_per_user": 1000,
        },
    )
    return obj

@pytest.mark.django_db
def test_relink_notification_sent_on_token_expiry(
    google_linked_user, company, email_template, settings_obj
):
    """Verify that send_campaign_paused_notification is called and actually sends an email."""
    # Ensure campaign is active and user has credits
    google_linked_user.is_campaign_active = True
    google_linked_user.credits_remaining = 10
    google_linked_user.save()

    with patch("apps.mailing.tasks.send_cv_email", side_effect=TokenExpiredError("invalid_grant")):
        # Run the task.
        process_mailing_queue()

    # The campaign should be paused
    google_linked_user.refresh_from_db()
    assert google_linked_user.is_campaign_active is False
    assert google_linked_user.campaign_pause_reason == "expired"

    # Check that an email was sent (django.core.mail.outbox)
    assert len(mail.outbox) == 1
    assert "FastJob: Tu campaña ha sido pausada" in mail.outbox[0].subject
    assert google_linked_user.email in mail.outbox[0].to
