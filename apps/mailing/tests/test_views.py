"""
Tests for the public mailing views: /cv/<token>/, /unsubscribe/<token>/.
Also exercises rate limiting (temporarily re-enabled per test via a mark).
"""
from unittest.mock import patch

import pytest
from django.urls import reverse

from apps.companies.models import Blacklist
from apps.mailing.models import MailingLog


@pytest.mark.django_db
def test_unsubscribe_adds_email_to_blacklist(client, google_linked_user, company, email_template):
    log = MailingLog.objects.create(
        user=google_linked_user, company=company, email_template=email_template
    )

    url = reverse("unsubscribe", args=[log.unsubscribe_token])
    resp = client.get(url)

    assert resp.status_code == 200
    assert Blacklist.objects.filter(email=company.email).exists()


@pytest.mark.django_db
def test_unsubscribe_is_idempotent(client, google_linked_user, company, email_template):
    log = MailingLog.objects.create(
        user=google_linked_user, company=company, email_template=email_template
    )
    url = reverse("unsubscribe", args=[log.unsubscribe_token])

    client.get(url)
    client.get(url)  # second click should not create a duplicate

    assert Blacklist.objects.filter(email=company.email).count() == 1


@pytest.mark.django_db
def test_unsubscribe_returns_404_for_unknown_token(client):
    import uuid
    url = reverse("unsubscribe", args=[uuid.uuid4()])
    resp = client.get(url)
    assert resp.status_code == 404


@pytest.mark.django_db
def test_cv_download_returns_404_for_unknown_token(client):
    import uuid
    url = reverse("cv_download", args=[uuid.uuid4()])
    resp = client.get(url)
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
    url = reverse("cv_download", args=[log.cv_download_token])
    resp = client.get(url)
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
