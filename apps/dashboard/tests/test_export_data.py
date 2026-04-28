"""C8 regression tests: GDPR Article 20 (data portability).

The endpoint must:
  - Require authentication.
  - Return a zip containing user.json, mailing_logs.csv, payments.csv, and
    each CV PDF under cvs/.
  - Be reachable via `reverse("export_data")` at `/dashboard/exportar-datos/`.
  - Return 429 on the second hit within 24h (rate-limit 1/d/user).
"""
import csv
import io
import json
import zipfile

import pytest
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.accounts.models import CV
from apps.mailing.models import MailingLog
from apps.payments.models import CreditPackage, StripePayment


@pytest.fixture(autouse=True)
def reset_ratelimit_cache():
    """django-ratelimit uses Django's cache to track keys. LocMem cache
    persists across tests in the same process — clear it so each test
    starts with a fresh limit window."""
    cache.clear()
    yield
    cache.clear()


def _read_zip_from_response(resp):
    """FileResponse streams from a tempfile; pull the bytes back into a
    BytesIO so zipfile can seek across it."""
    body = b"".join(resp.streaming_content)
    return zipfile.ZipFile(io.BytesIO(body))


@pytest.mark.django_db
def test_export_redirects_anonymous_user(client):
    resp = client.get(reverse("export_data"))
    # Anonymous → login redirect (302), NOT a 200 with someone else's data.
    assert resp.status_code in (302, 403)


@pytest.mark.django_db
def test_export_url_is_at_expected_path():
    """C8 acceptance: doc specifies `/dashboard/exportar-datos/`."""
    assert reverse("export_data") == "/dashboard/exportar-datos/"


@pytest.mark.django_db
def test_export_zip_contains_all_four_artefacts(client, user, settings):
    settings.RATELIMIT_ENABLE = False  # exercise the artefact contract, not the limiter

    cv = CV.objects.create(
        user=user,
        file=SimpleUploadedFile("alpha.pdf", b"%PDF-1.4 fake", content_type="application/pdf"),
        name="alpha",
    )
    user.active_cv = cv
    user.save(update_fields=["active_cv"])

    pkg = CreditPackage.objects.create(name="Starter", price_eur="9.99", credits=50)
    StripePayment.objects.create(
        user=user, package=pkg, stripe_session_id="cs_test_1",
        amount_eur="9.99", credits_granted=50,
        status=StripePayment.Status.COMPLETED,
    )
    MailingLog.objects.create(user=user, company=None, email_template=None,
                              status=MailingLog.Status.SENT)

    client.force_login(user)
    resp = client.get(reverse("export_data"))
    assert resp.status_code == 200
    assert resp["Content-Type"] == "application/zip"
    assert "attachment;" in resp["Content-Disposition"]

    zf = _read_zip_from_response(resp)
    names = set(zf.namelist())
    assert "user.json" in names
    assert "mailing_logs.csv" in names
    assert "payments.csv" in names
    # CV path uses `cvs/<pk>_<filename>` shape.
    cv_members = [n for n in names if n.startswith("cvs/")]
    assert len(cv_members) == 1
    assert cv_members[0].endswith(".pdf")

    # user.json: must include this user's email and pk
    user_payload = json.loads(zf.read("user.json"))
    assert user_payload["email"] == user.email
    assert user_payload["id"] == user.pk

    # mailing_logs.csv: header + 1 row
    log_rows = list(csv.reader(io.StringIO(zf.read("mailing_logs.csv").decode())))
    assert log_rows[0][0] == "id"
    assert len(log_rows) == 2

    # payments.csv: header + 1 row
    pay_rows = list(csv.reader(io.StringIO(zf.read("payments.csv").decode())))
    assert pay_rows[0][0] == "id"
    assert len(pay_rows) == 2
    assert pay_rows[1][3] == "completed"


@pytest.mark.django_db
def test_export_does_not_leak_other_users_data(client, user):
    """Defence-in-depth: a second user's CVs/logs/payments must NOT appear
    in this user's export."""
    from django.contrib.auth import get_user_model
    other = get_user_model().objects.create_user(
        username="other", email="other@example.com", password="pw"
    )
    CV.objects.create(user=other, file=SimpleUploadedFile("other.pdf", b"x"), name="other-cv")
    MailingLog.objects.create(user=other, status=MailingLog.Status.SENT)

    client.force_login(user)
    resp = client.get(reverse("export_data"))
    assert resp.status_code == 200
    zf = _read_zip_from_response(resp)
    # No CVs from the other user
    assert all("other" not in n for n in zf.namelist())
    # mailing_logs.csv has only the header (no rows for `user`)
    log_rows = list(csv.reader(io.StringIO(zf.read("mailing_logs.csv").decode())))
    assert len(log_rows) == 1  # header only


@pytest.mark.django_db
def test_export_rate_limited_to_one_per_day(client, user, settings):
    """Acceptance: second request within 24h returns 429."""
    settings.RATELIMIT_ENABLE = True
    client.force_login(user)

    first = client.get(reverse("export_data"))
    assert first.status_code == 200

    second = client.get(reverse("export_data"))
    assert second.status_code == 429
