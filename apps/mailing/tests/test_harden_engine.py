import pytest
from unittest.mock import patch, MagicMock
from datetime import timedelta
from django.utils import timezone
from apps.mailing.engine import (
    _refresh_microsoft_token, 
    _send_via_microsoft, 
    TokenExpiredError, 
    TokenRefreshTransientError
)
from apps.mailing.models import MailingLog, SystemSettings
from apps.mailing.tasks import process_mailing_queue

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
def test_refresh_triggers_within_10_min_buffer(microsoft_linked_user):
    token = microsoft_linked_user.socialaccount_set.first().socialtoken_set.first()
    # 5 minutes in the future should now trigger a refresh because it's < 10 minutes
    token.expires_at = timezone.now() + timedelta(minutes=5)
    token.save()

    with patch("apps.mailing.engine.requests.post") as mock_post:
        # Mock the refresh response
        mock_post.return_value = MagicMock(
            status_code=200, 
            json=lambda: {"access_token": "new", "expires_in": 3600}
        )
        _refresh_microsoft_token(token)

    assert mock_post.call_count == 1

@pytest.mark.django_db
def test_refresh_skips_if_11_min_remaining(microsoft_linked_user):
    token = microsoft_linked_user.socialaccount_set.first().socialtoken_set.first()
    # 11 minutes remaining > 10 minutes -> should NOT refresh
    token.expires_at = timezone.now() + timedelta(minutes=11)
    token.save()

    with patch("apps.mailing.engine.requests.post") as mock_post:
        _refresh_microsoft_token(token)

    mock_post.assert_not_called()

@pytest.mark.django_db
@pytest.mark.parametrize("status", [401, 403])
def test_send_microsoft_401_403_raises_expired(status):
    with patch("apps.mailing.engine.requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=status, text="auth error")
        with pytest.raises(TokenExpiredError):
            _send_via_microsoft("token", "to@x.com", "sub", "body", None)

@pytest.mark.django_db
@pytest.mark.parametrize("status", [429, 500, 503])
def test_send_microsoft_transient_raises_transient(status):
    with patch("apps.mailing.engine.requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=status, text="transient error")
        with pytest.raises(TokenRefreshTransientError):
            _send_via_microsoft("token", "to@x.com", "sub", "body", None)

@pytest.mark.django_db
def test_task_pauses_on_send_401(microsoft_linked_user, company, email_template, settings_obj):
    # Mock refresh to succeed but send to fail with 401
    with patch("apps.mailing.engine.requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=401, text="unauthorized")
        
        token = microsoft_linked_user.socialaccount_set.first().socialtoken_set.first()
        token.expires_at = timezone.now() + timedelta(hours=1)
        token.save()
        
        process_mailing_queue()

    microsoft_linked_user.refresh_from_db()
    assert microsoft_linked_user.is_campaign_active is False
    
    log = MailingLog.objects.first()
    assert log.status == MailingLog.Status.FAILED
    assert "auth error 401" in log.error_message

@pytest.mark.django_db
def test_task_skips_user_when_last_FAILED_send_too_recent(
    google_linked_user, company, email_template, settings_obj
):
    """Cooldown must apply even if the last attempt failed."""
    MailingLog.objects.create(
        user=google_linked_user,
        company=company,
        email_template=email_template,
        sent_at=timezone.now() - timedelta(minutes=2),
        status=MailingLog.Status.FAILED,
    )

    with patch("apps.mailing.tasks.send_cv_email") as mock_send:
        process_mailing_queue()

    mock_send.assert_not_called()
