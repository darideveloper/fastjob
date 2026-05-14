
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
    """Verify that send_relink_notification is called and actually sends an email."""
    # Ensure campaign is active and user has credits
    google_linked_user.is_campaign_active = True
    google_linked_user.credits_remaining = 10
    google_linked_user.save()

    with patch("apps.mailing.tasks.send_cv_email", side_effect=TokenExpiredError("invalid_grant")):
        # Run the task. We don't need to patch send_relink_notification.delay 
        # because we want to see if it actually sends the email (using CELERY_TASK_ALWAYS_EAGER if possible)
        # Actually, let's just patch the task itself to see if it's called, 
        # or better yet, run it synchronously if we can.
        process_mailing_queue()

    # The campaign should be paused
    google_linked_user.refresh_from_db()
    assert google_linked_user.is_campaign_active is False

    # Check that an email was sent (django.core.mail.outbox)
    # Note: Celery tasks in tests usually run synchronously if configured correctly, 
    # but here they might be async unless we use a fixture or setting.
    # If it was called via .delay(), it might not have run yet in the same thread.
    
    # Let's check the outbox.
    assert len(mail.outbox) == 1
    assert "Vuelve a conectar tu cuenta de correo" in mail.outbox[0].subject
    assert google_linked_user.email in mail.outbox[0].to
