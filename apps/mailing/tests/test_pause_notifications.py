from unittest.mock import MagicMock, patch
import pytest
from apps.mailing.engine import (
    QuotaExceededError,
    TokenExpiredError,
    _send_via_gmail,
    _send_via_microsoft,
)
from apps.mailing.tasks import process_mailing_queue
from apps.mailing.models import MailingLog

@pytest.mark.django_db
def test_gmail_quota_exceeded_detection():
    # Simulate a Gmail quota exceeded error
    fake_resp = MagicMock(status_code=403, text="Daily sending quota exceeded. (Mail sending)")
    with patch("apps.mailing.engine.requests.post", return_value=fake_resp):
        with pytest.raises(QuotaExceededError):
            _send_via_gmail("token", "from@ex.com", "to@ex.com", "sub", "html", None)

@pytest.mark.django_db
def test_microsoft_quota_exceeded_detection():
    # Simulate a Microsoft quota exceeded error
    fake_resp = MagicMock(status_code=400, text='{"error": {"code": "ErrorExceededMessageLimit"}}')
    with patch("apps.mailing.engine.requests.post", return_value=fake_resp):
        with pytest.raises(QuotaExceededError):
            _send_via_microsoft("token", "to@ex.com", "sub", "html", None)

@pytest.mark.django_db
def test_process_queue_pauses_for_quota(google_linked_user, company, email_template):
    # Setup: User is active, can send
    google_linked_user.is_campaign_active = True
    google_linked_user.credits_remaining = 10
    google_linked_user.save()
    
    # Mock send_cv_email to raise QuotaExceededError
    with patch("apps.mailing.tasks.send_cv_email", side_effect=QuotaExceededError("Quota reached")):
        # We also need to mock the lock so the task runs
        with patch("apps.mailing.tasks.cache.add", return_value=True):
            process_mailing_queue()
            
    google_linked_user.refresh_from_db()
    assert google_linked_user.is_campaign_active is False
    assert google_linked_user.campaign_pause_reason == "quota"
    
    # Verify log entry
    last_log = MailingLog.objects.filter(user=google_linked_user).last()
    assert last_log.status == MailingLog.Status.FAILED
    assert "Quota reached" in last_log.error_message

@pytest.mark.django_db
def test_process_queue_pauses_for_token_expired(google_linked_user, company, email_template):
    # Setup: User is active
    google_linked_user.is_campaign_active = True
    google_linked_user.save()
    
    # Mock send_cv_email to raise TokenExpiredError
    with patch("apps.mailing.tasks.send_cv_email", side_effect=TokenExpiredError("Token dead")):
        with patch("apps.mailing.tasks.cache.add", return_value=True):
            process_mailing_queue()
            
    google_linked_user.refresh_from_db()
    assert google_linked_user.is_campaign_active is False
    assert google_linked_user.campaign_pause_reason == "expired"
    
    # Verify log entry
    last_log = MailingLog.objects.filter(user=google_linked_user).last()
    assert last_log.status == MailingLog.Status.FAILED
    assert "Token dead" in last_log.error_message

@pytest.mark.django_db
def test_dashboard_index_shows_pause_reason(client, google_linked_user):
    google_linked_user.campaign_pause_reason = "quota"
    google_linked_user.save()
    
    client.force_login(google_linked_user)
    response = client.get("/dashboard/")
    assert response.status_code == 200
    assert "Límite diario alcanzado" in response.content.decode("utf-8")
    
    google_linked_user.campaign_pause_reason = "expired"
    google_linked_user.save()
    response = client.get("/dashboard/")
    assert "Sesión expirada" in response.content.decode("utf-8")
    assert "/accounts/login/" in response.content.decode("utf-8")

@pytest.mark.django_db
def test_toggle_campaign_clears_reason_even_on_failure(client, user):
    user.campaign_pause_reason = "quota"
    user.is_campaign_active = False
    # Ensure starting fails (no CV)
    user.active_cv = None
    user.save()
    
    client.force_login(user)
    # Action 'start' should fail validation but still clear the reason in the DB
    response = client.post("/dashboard/campana/", {"action": "start"})
    
    user.refresh_from_db()
    assert user.campaign_pause_reason == ""
    assert user.is_campaign_active is False
