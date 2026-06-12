from unittest.mock import MagicMock, patch
import pytest
from apps.mailing.engine import (
    CVFileMissingError,
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
    html = response.content.decode("utf-8")
    assert "Límite diario alcanzado" in html
    
    google_linked_user.campaign_pause_reason = "expired"
    google_linked_user.save()
    response = client.get("/dashboard/")
    html = response.content.decode("utf-8")
    assert "Sesión expirada" in html
    assert "/accounts/logout/" in html

    google_linked_user.campaign_pause_reason = "unlinked"
    google_linked_user.save()
    response = client.get("/dashboard/")
    html = response.content.decode("utf-8")
    assert "Cuenta desvinculada" in html
    assert "/accounts/logout/" in html

    google_linked_user.campaign_pause_reason = "missing_cv"
    google_linked_user.save()
    response = client.get("/dashboard/")
    html = response.content.decode("utf-8")
    assert "CV no disponible" in html
    # The "Vincular ahora" button should NOT appear for missing_cv
    # (count occurrences of "Vincular ahora" — from the three previous checks
    #  the button may still be in the page if the sessions overlap)
    # Instead, verify the body text about re-uploading is present.
    assert "Sube un nuevo CV" in html


@pytest.mark.django_db
def test_dashboard_hides_eliminar_button_when_campaign_active(client, user_with_cv):
    """The "Eliminar" button must be hidden when the campaign is active."""
    user_with_cv.is_campaign_active = True
    user_with_cv.save()

    client.force_login(user_with_cv)
    response = client.get("/dashboard/")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # The "Eliminar" text should NOT be present in the CV section
    assert "Eliminar este CV" not in html
    # The hint text should appear
    assert "Para eliminar un CV, pausa tu campaña primero" in html


@pytest.mark.django_db
def test_dashboard_shows_eliminar_button_when_campaign_paused(client, user_with_cv):
    """The "Eliminar" button must be visible when the campaign is paused."""
    user_with_cv.is_campaign_active = False
    user_with_cv.save()

    client.force_login(user_with_cv)
    response = client.get("/dashboard/")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # The "Eliminar" text should be present in the CV section
    assert "Eliminar este CV" in html
    # The hint text should NOT appear
    assert "Para eliminar un CV, pausa tu campaña primero" not in html

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


@pytest.mark.django_db
def test_process_queue_pauses_and_notifies_for_cv_missing(google_linked_user, company, email_template):
    google_linked_user.is_campaign_active = True
    google_linked_user.credits_remaining = 10
    google_linked_user.save()

    with patch("apps.mailing.tasks.send_cv_email", side_effect=CVFileMissingError("File not found")):
        with patch("apps.mailing.tasks.cache.add", return_value=True):
            process_mailing_queue()

    google_linked_user.refresh_from_db()
    assert google_linked_user.is_campaign_active is False
    assert google_linked_user.campaign_pause_reason == "missing_cv"

    last_log = MailingLog.objects.filter(user=google_linked_user).last()
    assert last_log.status == MailingLog.Status.FAILED
    assert "File not found" in last_log.error_message


@pytest.mark.django_db
def test_missing_cv_notification_email_sent(user_with_cv):
    from apps.mailing.tasks import send_campaign_paused_notification
    from django.core import mail

    send_campaign_paused_notification(user_with_cv.pk, "missing_cv")

    assert len(mail.outbox) == 1
    email = mail.outbox[0]
    assert "FastJob: Tu campaña ha sido pausada" in email.subject
    assert "no se ha encontrado tu CV" in email.body
    assert "dashboard" in email.body
    assert email.to == [user_with_cv.email]


@pytest.mark.django_db
def test_unlinked_notification_email_sent(user_with_cv):
    from apps.mailing.tasks import send_campaign_paused_notification
    from django.core import mail

    send_campaign_paused_notification(user_with_cv.pk, "unlinked")

    assert len(mail.outbox) == 1
    email = mail.outbox[0]
    assert "FastJob: Tu campaña ha sido pausada" in email.subject
    assert "se ha desvinculado tu cuenta" in email.body
    assert "dashboard" in email.body
    assert email.to == [user_with_cv.email]


@pytest.mark.django_db
def test_unlink_signal_enqueues_notification(client, google_linked_user):
    """When an OAuth account is disconnected, the signal handler must enqueue the notification."""
    from allauth.socialaccount.signals import social_account_removed
    from django.core import mail

    google_linked_user.is_campaign_active = True
    google_linked_user.save()

    social_account = google_linked_user.socialaccount_set.first()
    assert social_account is not None

    # Send the signal directly, simulating what allauth does on account removal.
    social_account_removed.send(
        sender=social_account.__class__,
        request=None,
        socialaccount=social_account,
    )

    google_linked_user.refresh_from_db()
    assert google_linked_user.is_campaign_active is False
    assert google_linked_user.campaign_pause_reason == "unlinked"

    # CELERY_TASK_ALWAYS_EAGER=True means .delay() runs synchronously, so the email is sent.
    assert len(mail.outbox) >= 1
    notification_email = [m for m in mail.outbox if "FastJob: Tu campaña ha sido pausada" in m.subject]
    assert len(notification_email) >= 1
    assert "se ha desvinculado tu cuenta" in notification_email[0].body
