"""Tests for the new dashboard views: pagination, analytics, multi-CV, deletion."""
from datetime import timedelta

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import CV
from apps.mailing.models import MailingLog


@pytest.mark.django_db
def test_dashboard_paginates_mailing_logs(client, user_with_cv, company, email_template):
    for _ in range(25):
        MailingLog.objects.create(
            user=user_with_cv, company=company, email_template=email_template,
            status=MailingLog.Status.SENT,
        )
    client.force_login(user_with_cv)

    page1 = client.get(reverse("dashboard"))
    assert page1.status_code == 200
    assert len(page1.context["recent_logs"]) == 20
    assert page1.context["paginator"].num_pages == 2

    page2 = client.get(reverse("dashboard") + "?page=2")
    assert len(page2.context["recent_logs"]) == 5


@pytest.mark.django_db
def test_dashboard_analytics_counts(client, user_with_cv, company, email_template):
    now = timezone.now()
    # 3 sent today, 2 sent 3 days ago, 1 sent 10 days ago, 1 failed
    for _ in range(3):
        MailingLog.objects.create(
            user=user_with_cv, company=company, email_template=email_template,
            status=MailingLog.Status.SENT, sent_at=now,
        )
    for _ in range(2):
        MailingLog.objects.create(
            user=user_with_cv, company=company, email_template=email_template,
            status=MailingLog.Status.SENT, sent_at=now - timedelta(days=3),
        )
    MailingLog.objects.create(
        user=user_with_cv, company=company, email_template=email_template,
        status=MailingLog.Status.SENT, sent_at=now - timedelta(days=10),
    )
    MailingLog.objects.create(
        user=user_with_cv, company=company, email_template=email_template,
        status=MailingLog.Status.FAILED,
    )
    client.force_login(user_with_cv)
    resp = client.get(reverse("dashboard"))

    assert resp.context["sent_today"] == 3
    assert resp.context["sent_this_week"] == 5   # 3 + 2 (10-day-old excluded)
    assert resp.context["sent_count"] == 6       # all SENT
    assert resp.context["failed_count"] == 1


@pytest.mark.django_db
def test_upload_cv_creates_new_row_and_preserves_old(client, user_with_cv):
    original_cv = user_with_cv.active_cv
    client.force_login(user_with_cv)

    resp = client.post(reverse("upload_cv"), {
        "cv_file": SimpleUploadedFile("new.pdf", b"%PDF new", content_type="application/pdf"),
    })
    assert resp.status_code == 302
    user_with_cv.refresh_from_db()
    assert user_with_cv.cvs.count() == 2
    assert user_with_cv.active_cv.pk != original_cv.pk
    # The old CV is preserved
    assert CV.objects.filter(pk=original_cv.pk).exists()


@pytest.mark.django_db
def test_set_active_cv_switches_pointer(client, user_with_cv):
    second = CV.objects.create(
        user=user_with_cv,
        file=SimpleUploadedFile("b.pdf", b"%PDF b"),
        name="Second",
    )
    client.force_login(user_with_cv)
    resp = client.post(reverse("set_active_cv", args=[second.pk]))
    assert resp.status_code == 302
    user_with_cv.refresh_from_db()
    assert user_with_cv.active_cv_id == second.pk


@pytest.mark.django_db
def test_delete_cv_falls_back_to_newest_remaining(client, user_with_cv):
    cv_old = user_with_cv.active_cv
    cv_new = CV.objects.create(
        user=user_with_cv,
        file=SimpleUploadedFile("n.pdf", b"%PDF n"),
        name="Newer",
    )
    # Campaign must be paused before deletion (guard prevents deletion while active).
    user_with_cv.is_campaign_active = False
    user_with_cv.save(update_fields=["is_campaign_active"])
    client.force_login(user_with_cv)
    # Delete the active one — falls back to newest remaining.
    client.post(reverse("delete_cv", args=[cv_old.pk]))
    user_with_cv.refresh_from_db()
    assert user_with_cv.active_cv_id == cv_new.pk


@pytest.mark.django_db
def test_delete_last_cv_when_campaign_paused(client, user_with_cv):
    cv = user_with_cv.active_cv
    # Campaign must be paused before deletion.
    user_with_cv.is_campaign_active = False
    user_with_cv.save(update_fields=["is_campaign_active"])
    client.force_login(user_with_cv)
    client.post(reverse("delete_cv", args=[cv.pk]))
    user_with_cv.refresh_from_db()
    assert user_with_cv.active_cv is None
    # Campaign stays paused (was already False).
    assert user_with_cv.is_campaign_active is False


@pytest.mark.django_db
def test_delete_account_requires_matching_email(client, user_with_cv):
    client.force_login(user_with_cv)
    resp = client.post(reverse("delete_account"), {"confirm_email": "wrong@example.com"})
    assert resp.status_code == 302
    from django.contrib.auth import get_user_model
    assert get_user_model().objects.filter(pk=user_with_cv.pk).exists()


@pytest.mark.django_db
@pytest.mark.django_db
def test_upload_cv_ajax_success(client, user_with_cv):
    client.force_login(user_with_cv)
    resp = client.post(
        reverse("upload_cv"),
        {"cv_file": SimpleUploadedFile("new.pdf", b"%PDF new", content_type="application/pdf")},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    user_with_cv.refresh_from_db()
    assert user_with_cv.cvs.count() == 2
    assert user_with_cv.active_cv.name == ""


@pytest.mark.django_db
def test_upload_cv_ajax_no_file(client, user_with_cv):
    client.force_login(user_with_cv)
    resp = client.post(
        reverse("upload_cv"),
        {},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    assert resp.status_code == 400
    assert resp.json() == {"ok": False, "error": "Por favor selecciona un archivo PDF."}


@pytest.mark.django_db
def test_upload_cv_ajax_wrong_type(client, user_with_cv):
    client.force_login(user_with_cv)
    resp = client.post(
        reverse("upload_cv"),
        {"cv_file": SimpleUploadedFile("resume.txt", b"not a pdf", content_type="text/plain")},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    assert resp.status_code == 400
    assert resp.json() == {"ok": False, "error": "Solo se permiten archivos PDF."}


@pytest.mark.django_db
def test_upload_cv_ajax_oversize(client, user_with_cv):
    client.force_login(user_with_cv)
    resp = client.post(
        reverse("upload_cv"),
        {"cv_file": SimpleUploadedFile("big.pdf", b"x" * (10 * 1024 * 1024 + 1), content_type="application/pdf")},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    assert resp.status_code == 400
    assert resp.json() == {"ok": False, "error": "El archivo no puede superar los 10 MB."}


@pytest.mark.django_db
def test_upload_cv_non_ajax_fallback(client, user_with_cv):
    """Non-AJAX POST must still return redirect + flash message."""
    client.force_login(user_with_cv)

    # Error case
    resp = client.post(reverse("upload_cv"), {})
    assert resp.status_code == 302
    assert resp.url == reverse("dashboard")

    # Success case: start fresh (delete the fixture CV so we can count)
    user_with_cv.active_cv.delete()
    resp = client.post(reverse("upload_cv"), {
        "cv_file": SimpleUploadedFile("fallback.pdf", b"%PDF fallback", content_type="application/pdf"),
    })
    assert resp.status_code == 302
    assert resp.url == reverse("dashboard")
    user_with_cv.refresh_from_db()
    assert user_with_cv.cvs.count() == 1


def test_delete_account_removes_user_and_cvs(client, user_with_cv):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    pk = user_with_cv.pk
    client.force_login(user_with_cv)
    resp = client.post(reverse("delete_account"), {"confirm_email": user_with_cv.email})
    assert resp.status_code == 302
    assert not User.objects.filter(pk=pk).exists()
    assert CV.objects.filter(user_id=pk).count() == 0


@pytest.mark.django_db
def test_delete_cv_rejected_when_campaign_active(client, user_with_cv):
    """Server guard blocks CV deletion while campaign is active."""
    cv = user_with_cv.active_cv
    assert user_with_cv.is_campaign_active
    client.force_login(user_with_cv)
    resp = client.post(reverse("delete_cv", args=[cv.pk]), follow=True)

    messages_list = list(resp.context["messages"])
    assert any("primero pausa tu campaña" in str(m) for m in messages_list)
    user_with_cv.refresh_from_db()
    assert user_with_cv.active_cv_id == cv.pk
    assert user_with_cv.is_campaign_active


@pytest.mark.django_db
def test_delete_cv_allowed_when_campaign_paused(client, user_with_cv):
    """Deletion works normally when campaign is paused."""
    cv = user_with_cv.active_cv
    user_with_cv.is_campaign_active = False
    user_with_cv.save(update_fields=["is_campaign_active"])
    client.force_login(user_with_cv)
    resp = client.post(reverse("delete_cv", args=[cv.pk]))
    assert resp.status_code == 302

    user_with_cv.refresh_from_db()
    # When it's the only CV, active_cv becomes None and campaign stays False.
    assert user_with_cv.active_cv is None
    assert user_with_cv.is_campaign_active is False


@pytest.mark.django_db
def test_dashboard_displays_payment_history(client, user):
    from apps.payments.models import CreditPackage, StripePayment

    client.force_login(user)

    # 1. User has no payments: should render empty state
    resp = client.get(reverse("dashboard"))
    assert resp.status_code == 200
    assert "payments" in resp.context
    assert len(resp.context["payments"]) == 0
    assert "Aún no has realizado ninguna compra" in resp.content.decode()

    # 2. User has a completed payment: should show payment history table
    package = CreditPackage.objects.create(name="Paquete Súper", price_eur=9.99, credits=50)
    StripePayment.objects.create(
        user=user,
        package=package,
        stripe_session_id="cs_test_123",
        amount_eur=9.99,
        credits_granted=50,
        status=StripePayment.Status.COMPLETED,
    )

    resp = client.get(reverse("dashboard"))
    assert resp.status_code == 200
    assert len(resp.context["payments"]) == 1
    assert "Paquete Súper" in resp.content.decode()
    assert "+50 envíos" in resp.content.decode()
    assert "9,99 €" in resp.content.decode() or "9.99 €" in resp.content.decode()

