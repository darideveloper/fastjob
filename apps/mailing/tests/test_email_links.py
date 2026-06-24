"""Regression harness: every URL embedded in a system email MUST resolve to a
registered route via ``abs_url()``. If a route is renamed without updating the
task, the assertion fails (``NoReverseMatch`` or a literal-string mismatch).

Covers: welcome, payment_receipt, oauth_linked, low_credits_warning,
account_deleted, campaign_paused_notification, and the campaign engine's
unsubscribe_url (body placeholder + List-Unsubscribe header).
"""
from unittest.mock import MagicMock, patch

import pytest
from django.core import mail

from apps.accounts.tasks import (
    send_account_deleted_email,
    send_oauth_link_email,
    send_welcome_email,
)
from apps.core.urls import abs_url
from apps.mailing.engine import send_cv_email
from apps.mailing.models import MailingLog
from apps.mailing.tasks import (
    send_campaign_paused_notification,
    send_low_credits_warning,
)
from apps.payments.models import CreditPackage, StripePayment
from apps.payments.tasks import send_payment_receipt_email


def _html(msg):
    """Return the HTML alternative of an EmailMultiAlternatives message."""
    for content, mimetype in msg.alternatives:
        if mimetype == "text/html":
            return content
    raise AssertionError("No text/html alternative in message")


def _assert_no_string_concat(html):
    """Guard against a regression to f-string URL construction."""
    assert "settings.SITE_DOMAIN" not in html
    assert "{settings.SITE_SCHEME}://" not in html


@pytest.mark.django_db
def test_welcome_email_dashboard_url_resolves(user):
    send_welcome_email(user.pk)
    html = _html(mail.outbox[0])
    assert abs_url("dashboard") in html
    _assert_no_string_concat(html)


@pytest.mark.django_db
def test_payment_receipt_urls_resolve(user):
    package = CreditPackage.objects.create(name="Pro", price_eur=50, credits=50, is_active=True)
    payment = StripePayment.objects.create(
        user=user,
        package=package,
        stripe_session_id="cs_test_links",
        amount_eur=50,
        credits_granted=50,
        status=StripePayment.Status.COMPLETED,
    )
    send_payment_receipt_email(user.pk, payment.pk)
    html = _html(mail.outbox[0])
    assert abs_url("billing_portal") in html
    assert abs_url("dashboard") in html
    _assert_no_string_concat(html)


@pytest.mark.django_db
def test_oauth_linked_email_dashboard_url_resolves(user):
    send_oauth_link_email(user.pk, "google")
    html = _html(mail.outbox[0])
    assert abs_url("dashboard") in html
    _assert_no_string_concat(html)


@pytest.mark.django_db
def test_low_credits_warning_packages_url_resolves(user):
    send_low_credits_warning(user.pk)
    html = _html(mail.outbox[0])
    assert abs_url("payment_packages") in html
    _assert_no_string_concat(html)


@pytest.mark.django_db
def test_account_deleted_email_home_url_resolves(user):
    send_account_deleted_email(user.email)
    html = _html(mail.outbox[0])
    assert abs_url("home") in html
    _assert_no_string_concat(html)


@pytest.mark.django_db
def test_campaign_paused_notification_dashboard_url_resolves(user):
    send_campaign_paused_notification(user.pk, "quota")
    html = _html(mail.outbox[0])
    assert abs_url("dashboard") in html
    _assert_no_string_concat(html)


@pytest.mark.django_db
def test_campaign_engine_unsubscribe_url_resolves(google_linked_user, company, email_template):
    log = MailingLog.objects.create(
        user=google_linked_user,
        company=company,
        email_template=email_template,
    )
    with patch("apps.mailing.engine.requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=202)
        send_cv_email(google_linked_user, company, email_template, log)

    import base64
    from email import message_from_string

    raw = mock_post.call_args.kwargs["json"]["raw"]
    raw_padded = raw + "=" * (-len(raw) % 4)
    msg = message_from_string(base64.urlsafe_b64decode(raw_padded).decode())

    expected = abs_url("unsubscribe", log.unsubscribe_token)
    assert msg["List-Unsubscribe"].strip() == f"<{expected}>"
