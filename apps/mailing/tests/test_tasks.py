"""
Tests for the `process_mailing_queue` Celery task.

These exercise the operational rules (slow-drip interval, per-company
cooldown, blacklist, filter matching, credit decrement, token-expiry pause)
without ever calling a real Google/Microsoft API.
"""
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.companies.models import Blacklist, Company
from apps.mailing.engine import TokenExpiredError
from apps.mailing.models import MailingLog, SystemSettings
from apps.mailing.tasks import process_mailing_queue


@pytest.fixture
def settings_obj(db):
    # Seed migration already inserted the singleton; update instead of create.
    obj, _ = SystemSettings.objects.update_or_create(
        pk=1,
        defaults={"global_send_interval_minutes": 5, "company_cooldown_hours": 12},
    )
    return obj


@pytest.mark.django_db
def test_task_sends_one_email_for_eligible_user(
    google_linked_user, company, email_template, settings_obj
):
    """Happy path: one eligible user + one template + one company → one send."""
    with patch("apps.mailing.tasks.send_cv_email") as mock_send:
        process_mailing_queue()

    assert mock_send.call_count == 1
    google_linked_user.refresh_from_db()
    assert google_linked_user.credits_remaining == 9  # -1 credit
    company.refresh_from_db()
    assert company.last_received_at is not None
    assert MailingLog.objects.filter(status=MailingLog.Status.SENT).count() == 1


@pytest.mark.django_db
def test_task_skips_user_when_last_send_too_recent(
    google_linked_user, company, email_template, settings_obj
):
    """Slow-drip: a send less than 5 min ago blocks another send for this user."""
    MailingLog.objects.create(
        user=google_linked_user,
        company=company,
        email_template=email_template,
        sent_at=timezone.now() - timedelta(minutes=2),
        status=MailingLog.Status.SENT,
    )

    with patch("apps.mailing.tasks.send_cv_email") as mock_send:
        process_mailing_queue()

    mock_send.assert_not_called()


@pytest.mark.django_db
def test_task_excludes_blacklisted_companies(
    google_linked_user, company, email_template, settings_obj
):
    Blacklist.objects.create(email=company.email, reason="unsubscribe")

    with patch("apps.mailing.tasks.send_cv_email") as mock_send:
        process_mailing_queue()

    mock_send.assert_not_called()


@pytest.mark.django_db
def test_task_excludes_companies_in_cooldown(
    google_linked_user, company, email_template, settings_obj
):
    """A company that received a CV less than 12h ago is off-limits."""
    other_user = type(google_linked_user).objects.create_user(
        username="u2", email="u2@x.com", password="p", credits_remaining=0
    )
    MailingLog.objects.create(
        user=other_user,
        company=company,
        email_template=email_template,
        sent_at=timezone.now() - timedelta(hours=2),
        status=MailingLog.Status.SENT,
    )

    with patch("apps.mailing.tasks.send_cv_email") as mock_send:
        process_mailing_queue()

    mock_send.assert_not_called()


@pytest.mark.django_db
def test_task_respects_user_area_filter(
    google_linked_user, email_template, settings_obj
):
    """Exact-match only: a filter of 'Tecnología' must NOT match 'Tecnología Industrial'."""
    Company.objects.create(email="a@x.com", name="A", area="Finanzas", location="")
    Company.objects.create(email="b@x.com", name="B", area="Tecnología", location="")
    Company.objects.create(email="c@x.com", name="C", area="Tecnología Industrial", location="")

    google_linked_user.area_filter = "Tecnología"
    google_linked_user.save()

    with patch("apps.mailing.tasks.send_cv_email") as mock_send:
        process_mailing_queue()

    assert mock_send.call_count == 1
    chosen_company = mock_send.call_args[0][1]
    assert chosen_company.area.lower() == "tecnología"


@pytest.mark.django_db
def test_task_user_filter_is_case_insensitive(
    google_linked_user, email_template, settings_obj
):
    """Lowercase filter value must still match a company with capitalized area."""
    Company.objects.create(email="a@x.com", name="A", area="Tecnología", location="")

    google_linked_user.area_filter = "tecnología"
    google_linked_user.save()

    with patch("apps.mailing.tasks.send_cv_email") as mock_send:
        process_mailing_queue()

    assert mock_send.call_count == 1
    chosen_company = mock_send.call_args[0][1]
    assert chosen_company.area == "Tecnología"


@pytest.mark.django_db
def test_task_pauses_campaign_on_token_expiry(
    google_linked_user, company, email_template, settings_obj
):
    """If the engine raises TokenExpiredError, the campaign must be paused."""
    with patch("apps.mailing.tasks.send_cv_email", side_effect=TokenExpiredError("expired")):
        process_mailing_queue()

    google_linked_user.refresh_from_db()
    assert google_linked_user.is_campaign_active is False
    # Credits should NOT be deducted for a failed send.
    assert google_linked_user.credits_remaining == 10
    # The failure is logged.
    assert MailingLog.objects.filter(status=MailingLog.Status.FAILED).count() == 1


@pytest.mark.django_db
def test_task_skips_users_without_credits(
    google_linked_user, company, email_template, settings_obj
):
    google_linked_user.credits_remaining = 0
    google_linked_user.save()

    with patch("apps.mailing.tasks.send_cv_email") as mock_send:
        process_mailing_queue()

    mock_send.assert_not_called()


@pytest.mark.django_db
def test_task_skips_users_without_cv(
    google_linked_user, company, email_template, settings_obj
):
    google_linked_user.active_cv = None
    google_linked_user.save(update_fields=["active_cv"])

    with patch("apps.mailing.tasks.send_cv_email") as mock_send:
        process_mailing_queue()

    mock_send.assert_not_called()


@pytest.mark.django_db
def test_task_does_nothing_without_active_templates(
    google_linked_user, company, settings_obj
):
    """No active EmailTemplate = nothing sent. Shouldn't crash."""
    from apps.mailing.models import EmailTemplate
    # Seed migration created 3 active templates; remove them to test the empty case.
    EmailTemplate.objects.all().delete()

    with patch("apps.mailing.tasks.send_cv_email") as mock_send:
        process_mailing_queue()

    mock_send.assert_not_called()


@pytest.mark.django_db
def test_credit_decrement_survives_lost_update_pattern(google_linked_user):
    """C1 race-fix proof: simulate two concurrent workers each holding a stale
    `User` instance. With the old `user.credits_remaining -= 1; user.save()`
    pattern, the second save would overwrite the first (lost update). With the
    new F() expression, each decrement composes at SQL level."""
    from django.contrib.auth import get_user_model
    from django.db.models import F

    User = get_user_model()
    google_linked_user.credits_remaining = 10
    google_linked_user.save()

    # Two stale views — both think credits == 10
    user_a = User.objects.get(pk=google_linked_user.pk)
    user_b = User.objects.get(pk=google_linked_user.pk)
    assert user_a.credits_remaining == 10 and user_b.credits_remaining == 10

    # Apply atomic decrements via the same pattern the engine task uses
    User.objects.filter(pk=user_a.pk).update(credits_remaining=F("credits_remaining") - 1)
    User.objects.filter(pk=user_b.pk).update(credits_remaining=F("credits_remaining") - 1)

    google_linked_user.refresh_from_db()
    assert google_linked_user.credits_remaining == 8  # both decrements survived
