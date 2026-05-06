"""
Tests for the public mailing views: /cv/<token>/, /unsubscribe/<token>/.
Also exercises rate limiting (temporarily re-enabled per test via a mark).
"""
import uuid
from unittest.mock import patch

import pytest
from django.urls import reverse

from apps.companies.models import Blacklist
from apps.mailing.models import MailingLog


# ---------------------------------------------------------------------------
# Unsubscribe view — GET (confirm page, no mutation)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_unsubscribe_get_does_not_blacklist(client, google_linked_user, company, email_template):
    log = MailingLog.objects.create(
        user=google_linked_user, company=company, email_template=email_template
    )
    url = reverse("unsubscribe", args=[log.unsubscribe_token])
    resp = client.get(url)

    assert resp.status_code == 200
    assert Blacklist.objects.count() == 0
    assert b"Confirmar baja" in resp.content


@pytest.mark.django_db
def test_unsubscribe_get_renders_confirm_template(client, google_linked_user, company, email_template):
    log = MailingLog.objects.create(
        user=google_linked_user, company=company, email_template=email_template
    )
    url = reverse("unsubscribe", args=[log.unsubscribe_token])
    resp = client.get(url)

    assert resp.status_code == 200
    assert b"unsubscribe_confirm" in resp.content or b"Confirmar" in resp.content


# ---------------------------------------------------------------------------
# Unsubscribe view — POST (commit unsubscribe)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_unsubscribe_post_creates_blacklist_row(client, google_linked_user, company, email_template):
    log = MailingLog.objects.create(
        user=google_linked_user, company=company, email_template=email_template
    )
    url = reverse("unsubscribe", args=[log.unsubscribe_token])
    resp = client.post(url)

    assert resp.status_code == 200
    assert Blacklist.objects.filter(email=company.email).exists()

    log.refresh_from_db()
    assert log.unsubscribed_at is not None


@pytest.mark.django_db
def test_unsubscribe_post_preserves_first_opt_out_timestamp(
    client, google_linked_user, company, email_template
):
    """Idempotent POST: replays preserve the first opt-out timestamp.

    Spec: `MailingLog.unsubscribed_at` captures when the recipient FIRST opted
    out, not the moment of the latest replay. Mailbox-provider one-click
    retries, double-clicks, and scanner-issued duplicates must not advance it.
    """
    log = MailingLog.objects.create(
        user=google_linked_user, company=company, email_template=email_template
    )
    url = reverse("unsubscribe", args=[log.unsubscribe_token])

    client.post(url)
    log.refresh_from_db()
    first_ts = log.unsubscribed_at

    client.post(url)
    log.refresh_from_db()

    # Blacklist still has exactly one row, unsubscribed_at is NOT updated on second call.
    assert Blacklist.objects.filter(email=company.email).count() == 1
    assert log.unsubscribed_at == first_ts


@pytest.mark.django_db
def test_unsubscribe_post_one_click_without_csrf_token(client, google_linked_user, company, email_template):
    """RFC 8058 one-click POST must succeed even without a CSRF cookie/token."""
    log = MailingLog.objects.create(
        user=google_linked_user, company=company, email_template=email_template
    )
    url = reverse("unsubscribe", args=[log.unsubscribe_token])

    # enforce_csrf_checks=True simulates a strict CSRF client.
    from django.test import Client
    strict_client = Client(enforce_csrf_checks=True)
    resp = strict_client.post(url)

    assert resp.status_code == 200
    assert Blacklist.objects.filter(email=company.email).exists()


@pytest.mark.django_db
def test_unsubscribe_invalid_token_returns_404(client):
    url = reverse("unsubscribe", args=[uuid.uuid4()])
    assert client.get(url).status_code == 404
    assert client.post(url).status_code == 404


@pytest.mark.django_db
def test_unsubscribe_rate_limit_blocks_after_threshold(
    client, google_linked_user, company, email_template, settings
):
    """With ratelimit enabled, the 11th GET within an hour returns 429."""
    settings.RATELIMIT_ENABLE = True

    from django.core.cache import cache
    cache.clear()

    log = MailingLog.objects.create(
        user=google_linked_user, company=company, email_template=email_template
    )
    url = reverse("unsubscribe", args=[log.unsubscribe_token])

    for _ in range(10):
        client.get(url)
    final = client.get(url)
    assert final.status_code == 429


# ---------------------------------------------------------------------------
# CV download — blacklist gate
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_cv_download_blocked_after_unsubscribe(
    client, google_linked_user, company, email_template
):
    Blacklist.objects.create(email=company.email)
    log = MailingLog.objects.create(
        user=google_linked_user, company=company, email_template=email_template
    )
    with patch("boto3.client") as mock_boto:
        resp = client.get(reverse("cv_download", args=[log.cv_download_token]))

    assert resp.status_code == 410
    mock_boto.assert_not_called()


@pytest.mark.django_db
def test_cv_download_returns_404_for_unknown_token(client):
    resp = client.get(reverse("cv_download", args=[uuid.uuid4()]))
    assert resp.status_code == 404


@pytest.mark.django_db
def test_cv_download_shows_error_when_user_has_no_cv(
    client, google_linked_user, company, email_template
):
    google_linked_user.active_cv = None
    google_linked_user.save(update_fields=["active_cv"])

    log = MailingLog.objects.create(
        user=google_linked_user, company=company, email_template=email_template
    )
    resp = client.get(reverse("cv_download", args=[log.cv_download_token]))
    assert resp.status_code == 404


@pytest.mark.django_db
def test_cv_download_redirects_to_signed_url(
    client, google_linked_user, company, email_template
):
    log = MailingLog.objects.create(
        user=google_linked_user, company=company, email_template=email_template
    )
    fake_signed = "https://signed.example.com/cv.pdf?sig=abc"

    with patch("boto3.client") as mock_boto:
        mock_boto.return_value.generate_presigned_url.return_value = fake_signed
        resp = client.get(reverse("cv_download", args=[log.cv_download_token]))

    assert resp.status_code == 302
    assert resp.url == fake_signed
    # H13: presigned-URL redirect must NOT be cached anywhere — a CDN or
    # browser cache could otherwise replay the redirect after the token
    # has been revoked or the rate-limit hit.
    assert resp["Cache-Control"] == "no-store"


@pytest.mark.django_db
def test_unsubscribe_log_hash_matches_canonical_blacklist_key(
    client, google_linked_user, company, email_template, caplog
):
    """The structured `outcome=unsubscribed` log's company_email_sha256 MUST equal
    sha256(email.strip().lower()) — the same normalization Blacklist.add applies —
    so analytics joins between the log stream and Blacklist.email succeed even
    when the snapshot has stray whitespace or mixed case.
    """
    import hashlib
    import logging

    log = MailingLog.objects.create(
        user=google_linked_user,
        company=company,
        email_template=email_template,
        company_email_snapshot="  Contact@Empresa.ES  ",
    )

    caplog.set_level(logging.INFO, logger="apps.mailing.views")

    url = reverse("unsubscribe", args=[log.unsubscribe_token])
    resp = client.post(url)
    assert resp.status_code == 200

    expected_hash = hashlib.sha256(b"contact@empresa.es").hexdigest()

    structured = [r for r in caplog.records if getattr(r, "outcome", None) == "unsubscribed"]
    assert len(structured) == 1
    rec = structured[0]
    assert rec.company_email_sha256 == expected_hash

    # The matching Blacklist row uses the same canonical key — proving the hash
    # an analytics consumer would compute against Blacklist.email matches the log.
    bl = Blacklist.objects.get(email="contact@empresa.es")
    assert hashlib.sha256(bl.email.encode()).hexdigest() == expected_hash


@pytest.mark.django_db
def test_rate_limit_returns_429(client, google_linked_user, company, email_template, settings):
    """With ratelimit enabled, the 31st request in one hour gets 429."""
    settings.RATELIMIT_ENABLE = True

    # Reset the ratelimit cache between tests (LocMem is process-local but persists
    # across test functions in the same process).
    from django.core.cache import cache
    cache.clear()

    log = MailingLog.objects.create(
        user=google_linked_user, company=company, email_template=email_template
    )
    url = reverse("unsubscribe", args=[log.unsubscribe_token])

    # Unsubscribe limit is 10/h.
    for _ in range(10):
        client.get(url)
    final = client.get(url)
    assert final.status_code == 429
