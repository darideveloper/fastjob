"""
Tests for apps/mailing/engine.py.

These are the highest-priority tests in the codebase: the engine talks to
Google and Microsoft APIs on behalf of thousands of users. A silent failure
here means every customer stops getting sends.

We mock `requests.post` so no network calls actually fire.
"""
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone

from apps.mailing.engine import (
    TokenExpiredError,
    _refresh_google_token,
    _refresh_microsoft_token,
    send_cv_email,
)
from apps.mailing.models import MailingLog


# ---------------------------------------------------------------------------
# Google token refresh
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_google_token_refresh_returns_cached_when_still_valid(google_linked_user):
    token = google_linked_user.socialaccount_set.first().socialtoken_set.first()
    original = token.token

    # No HTTP call should happen if the token is not near expiry.
    with patch("apps.mailing.engine.requests.post") as mock_post:
        result = _refresh_google_token(token)

    assert result == original
    mock_post.assert_not_called()


@pytest.mark.django_db
def test_google_token_refresh_fetches_new_when_expired(google_linked_user):
    token = google_linked_user.socialaccount_set.first().socialtoken_set.first()
    token.expires_at = timezone.now() - timedelta(minutes=5)
    token.save()

    fake_resp = MagicMock(status_code=200)
    fake_resp.json.return_value = {"access_token": "new-token", "expires_in": 3600}

    with patch("apps.mailing.engine.requests.post", return_value=fake_resp) as mock_post:
        result = _refresh_google_token(token)

    assert result == "new-token"
    token.refresh_from_db()
    assert token.token == "new-token"
    assert token.expires_at > timezone.now()
    mock_post.assert_called_once()


@pytest.mark.django_db
def test_google_token_refresh_raises_when_api_returns_error(google_linked_user):
    token = google_linked_user.socialaccount_set.first().socialtoken_set.first()
    token.expires_at = timezone.now() - timedelta(minutes=5)
    token.save()

    fake_resp = MagicMock(status_code=400, text="invalid_grant")
    with patch("apps.mailing.engine.requests.post", return_value=fake_resp):
        with pytest.raises(TokenExpiredError):
            _refresh_google_token(token)


# ---------------------------------------------------------------------------
# Microsoft token refresh
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_microsoft_token_refresh_fetches_new_when_expired(microsoft_linked_user):
    token = microsoft_linked_user.socialaccount_set.first().socialtoken_set.first()
    token.expires_at = timezone.now() - timedelta(minutes=5)
    token.save()

    fake_resp = MagicMock(status_code=200)
    fake_resp.json.return_value = {"access_token": "ms-new", "expires_in": 3600}

    with patch("apps.mailing.engine.requests.post", return_value=fake_resp):
        result = _refresh_microsoft_token(token)

    assert result == "ms-new"


@pytest.mark.django_db
def test_microsoft_token_refresh_raises_when_api_fails(microsoft_linked_user):
    token = microsoft_linked_user.socialaccount_set.first().socialtoken_set.first()
    token.expires_at = timezone.now() - timedelta(minutes=5)
    token.save()

    fake_resp = MagicMock(status_code=401, text="AADSTS...")
    with patch("apps.mailing.engine.requests.post", return_value=fake_resp):
        with pytest.raises(TokenExpiredError):
            _refresh_microsoft_token(token)


# ---------------------------------------------------------------------------
# End-to-end send (mocked HTTP)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_send_cv_email_via_google_success(google_linked_user, company, email_template):
    log = MailingLog.objects.create(
        user=google_linked_user,
        company=company,
        email_template=email_template,
    )

    with patch("apps.mailing.engine.requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        send_cv_email(google_linked_user, company, email_template, log)

    # The only call should be to Gmail, not to the refresh endpoint (token valid).
    assert mock_post.call_count == 1
    call_url = mock_post.call_args[0][0]
    assert "gmail.googleapis.com" in call_url


@pytest.mark.django_db
def test_send_cv_email_via_microsoft_success(microsoft_linked_user, company, email_template):
    log = MailingLog.objects.create(
        user=microsoft_linked_user,
        company=company,
        email_template=email_template,
    )

    with patch("apps.mailing.engine.requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=202)
        send_cv_email(microsoft_linked_user, company, email_template, log)

    assert mock_post.call_count == 1
    call_url = mock_post.call_args[0][0]
    assert "graph.microsoft.com" in call_url


@pytest.mark.django_db
def test_send_cv_email_raises_when_no_social_account(user_with_cv, company, email_template):
    """A user without any OAuth link should raise TokenExpiredError."""
    log = MailingLog.objects.create(
        user=user_with_cv,
        company=company,
        email_template=email_template,
    )
    with pytest.raises(TokenExpiredError):
        send_cv_email(user_with_cv, company, email_template, log)


@pytest.mark.django_db
def test_send_cv_email_propagates_gmail_api_failure(google_linked_user, company, email_template):
    """If Gmail returns 500, the engine should re-raise so the task can log it."""
    log = MailingLog.objects.create(
        user=google_linked_user,
        company=company,
        email_template=email_template,
    )

    with patch("apps.mailing.engine.requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=500, text="internal error")
        with pytest.raises(Exception, match="Gmail API error"):
            send_cv_email(google_linked_user, company, email_template, log)


# ---------------------------------------------------------------------------
# H8 — token-refresh failure must NOT log raw response body
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_google_refresh_failure_log_excludes_raw_body(google_linked_user, caplog):
    token = google_linked_user.socialaccount_set.first().socialtoken_set.first()
    token.expires_at = timezone.now() - timedelta(minutes=5)
    token.save()

    fake_resp = MagicMock(status_code=400)
    fake_resp.json.return_value = {"error": "invalid_grant", "error_description": "Token revoked"}
    fake_resp.text = "SECRET_BODY_SHOULD_NOT_LEAK"

    import logging
    caplog.set_level(logging.ERROR, logger="apps.mailing.engine")

    with patch("apps.mailing.engine.requests.post", return_value=fake_resp):
        with pytest.raises(TokenExpiredError):
            _refresh_google_token(token)

    log_text = "\n".join(r.getMessage() for r in caplog.records)
    assert "SECRET_BODY_SHOULD_NOT_LEAK" not in log_text
    assert "invalid_grant" in log_text  # the parsed error code is OK to log
    assert "status=400" in log_text


@pytest.mark.django_db
def test_microsoft_refresh_failure_log_excludes_raw_body(microsoft_linked_user, caplog):
    token = microsoft_linked_user.socialaccount_set.first().socialtoken_set.first()
    token.expires_at = timezone.now() - timedelta(minutes=5)
    token.save()

    fake_resp = MagicMock(status_code=401)
    fake_resp.json.return_value = {"error": "invalid_grant"}
    fake_resp.text = "AADSTS_LEAKY_BODY"

    import logging
    caplog.set_level(logging.ERROR, logger="apps.mailing.engine")

    with patch("apps.mailing.engine.requests.post", return_value=fake_resp):
        with pytest.raises(TokenExpiredError):
            _refresh_microsoft_token(token)

    log_text = "\n".join(r.getMessage() for r in caplog.records)
    assert "AADSTS_LEAKY_BODY" not in log_text


# ---------------------------------------------------------------------------
# H9 — CRLF in subject must be stripped before MIME assembly
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_send_cv_email_strips_crlf_from_subject(google_linked_user, company, email_template):
    """A staff template with `\\r\\nBcc:` in the subject must not smuggle headers."""
    email_template.subject = "Hola {company_name}\r\nBcc: attacker@evil.com"
    email_template.save()

    log = MailingLog.objects.create(
        user=google_linked_user,
        company=company,
        email_template=email_template,
    )

    with patch("apps.mailing.engine.requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        send_cv_email(google_linked_user, company, email_template, log)

    # Decode the base64-encoded raw MIME message that the engine sent to Gmail
    # and parse it as a real email so we check actual headers, not text content.
    import base64
    from email import message_from_string

    raw = mock_post.call_args.kwargs["json"]["raw"]
    raw_padded = raw + "=" * (-len(raw) % 4)
    mime_text = base64.urlsafe_b64decode(raw_padded).decode()
    msg = message_from_string(mime_text)

    # No Bcc header was smuggled in (the CRLF in the subject was stripped, so
    # `Bcc: attacker@evil.com` stayed inside the Subject value as plain text).
    assert msg["Bcc"] is None
    assert msg["To"] == "hr@acme.com"
    assert "\r" not in msg["Subject"] and "\n" not in msg["Subject"]
