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
    TokenRefreshTransientError,
    _classify_refresh_failure,
    _get_social_token,
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


# ===========================================================================
# harden-oauth-token-lifecycle — tests for the new behavior.
# ===========================================================================

# ---------------------------------------------------------------------------
# §7.2/§7.3 — refresh-token rotation persistence
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_microsoft_refresh_persists_rotated_refresh_token(microsoft_linked_user):
    token = microsoft_linked_user.socialaccount_set.first().socialtoken_set.first()
    token.token_secret = "old-refresh-abc"
    token.expires_at = timezone.now() - timedelta(minutes=5)
    token.save()

    fake_resp = MagicMock(status_code=200)
    fake_resp.json.return_value = {
        "access_token": "new-access",
        "refresh_token": "new-refresh-xyz",
        "expires_in": 3600,
    }

    with patch("apps.mailing.engine.requests.post", return_value=fake_resp):
        result = _refresh_microsoft_token(token)

    assert result == "new-access"
    token.refresh_from_db()
    assert token.token == "new-access"
    assert token.token_secret == "new-refresh-xyz"


@pytest.mark.django_db
def test_google_refresh_persists_refresh_token_when_present(google_linked_user):
    token = google_linked_user.socialaccount_set.first().socialtoken_set.first()
    token.token_secret = "old-google-refresh"
    token.expires_at = timezone.now() - timedelta(minutes=5)
    token.save()

    fake_resp = MagicMock(status_code=200)
    fake_resp.json.return_value = {
        "access_token": "g-new",
        "refresh_token": "g-new-refresh",
        "expires_in": 3600,
    }

    with patch("apps.mailing.engine.requests.post", return_value=fake_resp):
        _refresh_google_token(token)

    token.refresh_from_db()
    assert token.token_secret == "g-new-refresh"


@pytest.mark.django_db
def test_google_refresh_preserves_existing_refresh_token_when_absent(google_linked_user):
    """Google usually does NOT return refresh_token on refresh — must not null it out."""
    token = google_linked_user.socialaccount_set.first().socialtoken_set.first()
    token.token_secret = "google-refresh-keep"
    token.expires_at = timezone.now() - timedelta(minutes=5)
    token.save()

    fake_resp = MagicMock(status_code=200)
    fake_resp.json.return_value = {"access_token": "g-new", "expires_in": 3600}

    with patch("apps.mailing.engine.requests.post", return_value=fake_resp):
        _refresh_google_token(token)

    token.refresh_from_db()
    assert token.token_secret == "google-refresh-keep"
    assert token.token == "g-new"


# ---------------------------------------------------------------------------
# §7.4 — cache-hit short-circuit
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_refresh_skips_when_unexpired_within_skew_window(google_linked_user):
    token = google_linked_user.socialaccount_set.first().socialtoken_set.first()
    token.expires_at = timezone.now() + timedelta(minutes=5)  # well clear of 60s skew
    token.save()

    with patch("apps.mailing.engine.requests.post") as mock_post:
        result = _refresh_google_token(token)

    mock_post.assert_not_called()
    assert result == token.token


# ---------------------------------------------------------------------------
# §7.5–§7.8 — transient-vs-terminal error classification
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@pytest.mark.parametrize("status", [500, 502, 503, 504])
def test_5xx_raises_transient_error_google(google_linked_user, status):
    token = google_linked_user.socialaccount_set.first().socialtoken_set.first()
    token.expires_at = timezone.now() - timedelta(minutes=5)
    token.save()

    fake_resp = MagicMock(status_code=status)
    fake_resp.json.return_value = {"error": "backendError"}

    with patch("apps.mailing.engine.requests.post", return_value=fake_resp):
        with pytest.raises(TokenRefreshTransientError):
            _refresh_google_token(token)


@pytest.mark.django_db
def test_5xx_raises_transient_error_microsoft(microsoft_linked_user):
    token = microsoft_linked_user.socialaccount_set.first().socialtoken_set.first()
    token.expires_at = timezone.now() - timedelta(minutes=5)
    token.save()

    fake_resp = MagicMock(status_code=503)
    fake_resp.json.return_value = {"error": "service_unavailable"}

    with patch("apps.mailing.engine.requests.post", return_value=fake_resp):
        with pytest.raises(TokenRefreshTransientError):
            _refresh_microsoft_token(token)


@pytest.mark.django_db
def test_invalid_grant_raises_token_expired_google(google_linked_user):
    token = google_linked_user.socialaccount_set.first().socialtoken_set.first()
    token.expires_at = timezone.now() - timedelta(minutes=5)
    token.save()

    fake_resp = MagicMock(status_code=400)
    fake_resp.json.return_value = {"error": "invalid_grant"}

    with patch("apps.mailing.engine.requests.post", return_value=fake_resp):
        with pytest.raises(TokenExpiredError):
            _refresh_google_token(token)


@pytest.mark.django_db
def test_invalid_grant_raises_token_expired_microsoft(microsoft_linked_user):
    token = microsoft_linked_user.socialaccount_set.first().socialtoken_set.first()
    token.expires_at = timezone.now() - timedelta(minutes=5)
    token.save()

    fake_resp = MagicMock(status_code=400)
    fake_resp.json.return_value = {"error": "invalid_grant"}

    with patch("apps.mailing.engine.requests.post", return_value=fake_resp):
        with pytest.raises(TokenExpiredError):
            _refresh_microsoft_token(token)


@pytest.mark.django_db
def test_429_raises_transient_error(google_linked_user):
    token = google_linked_user.socialaccount_set.first().socialtoken_set.first()
    token.expires_at = timezone.now() - timedelta(minutes=5)
    token.save()

    fake_resp = MagicMock(status_code=429)
    fake_resp.json.return_value = {"error": "rate_limited"}

    with patch("apps.mailing.engine.requests.post", return_value=fake_resp):
        with pytest.raises(TokenRefreshTransientError):
            _refresh_google_token(token)


@pytest.mark.django_db
def test_network_timeout_raises_transient_error(google_linked_user):
    token = google_linked_user.socialaccount_set.first().socialtoken_set.first()
    token.expires_at = timezone.now() - timedelta(minutes=5)
    token.save()

    import requests as _r
    with patch("apps.mailing.engine.requests.post", side_effect=_r.Timeout("boom")):
        with pytest.raises(TokenRefreshTransientError):
            _refresh_google_token(token)


@pytest.mark.django_db
def test_connection_error_raises_transient_error(microsoft_linked_user):
    token = microsoft_linked_user.socialaccount_set.first().socialtoken_set.first()
    token.expires_at = timezone.now() - timedelta(minutes=5)
    token.save()

    import requests as _r
    with patch("apps.mailing.engine.requests.post", side_effect=_r.ConnectionError("dns")):
        with pytest.raises(TokenRefreshTransientError):
            _refresh_microsoft_token(token)


@pytest.mark.django_db
def test_401_raises_token_expired(microsoft_linked_user):
    """Provider revoked access — must be terminal, not transient."""
    token = microsoft_linked_user.socialaccount_set.first().socialtoken_set.first()
    token.expires_at = timezone.now() - timedelta(minutes=5)
    token.save()

    fake_resp = MagicMock(status_code=401)
    fake_resp.json.return_value = {"error": "AADSTS50173"}

    with patch("apps.mailing.engine.requests.post", return_value=fake_resp):
        with pytest.raises(TokenExpiredError):
            _refresh_microsoft_token(token)


# ---------------------------------------------------------------------------
# Direct unit tests for the classifier — independent of provider plumbing
# so a future provider addition can rely on the same mapping table.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("status", [500, 502, 503, 504, 599])
def test_classifier_5xx_is_transient(status):
    fake = MagicMock(status_code=status)
    fake.json.return_value = {}
    assert isinstance(_classify_refresh_failure(fake), TokenRefreshTransientError)


def test_classifier_429_is_transient():
    fake = MagicMock(status_code=429)
    fake.json.return_value = {}
    assert isinstance(_classify_refresh_failure(fake), TokenRefreshTransientError)


@pytest.mark.parametrize("err", ["invalid_grant", "invalid_client", "unauthorized_client"])
def test_classifier_known_oauth_errors_are_terminal(err):
    fake = MagicMock(status_code=400)
    fake.json.return_value = {"error": err}
    assert isinstance(_classify_refresh_failure(fake), TokenExpiredError)


def test_classifier_unknown_4xx_is_terminal_conservative():
    """Unknown failures are treated as terminal so users get the relink email."""
    fake = MagicMock(status_code=400)
    fake.json.return_value = {"error": "weird_brand_new_thing"}
    assert isinstance(_classify_refresh_failure(fake), TokenExpiredError)


def test_classifier_timeout_exception_is_transient():
    import requests as _r
    assert isinstance(
        _classify_refresh_failure(_r.Timeout("nope")),
        TokenRefreshTransientError,
    )


def test_classifier_connection_error_is_transient():
    import requests as _r
    assert isinstance(
        _classify_refresh_failure(_r.ConnectionError("dns")),
        TokenRefreshTransientError,
    )


# ---------------------------------------------------------------------------
# §7.11 — deterministic multi-provider selection
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_user_with_two_linked_providers_uses_most_recent(google_linked_user):
    """A user who linked Microsoft AFTER Google should send via Microsoft."""
    from datetime import timedelta as _td
    from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
    from django.contrib.sites.models import Site

    # The fixture's Google account was created "just now". Backdate it so the
    # Microsoft account we're about to create is unambiguously more recent.
    google_account = google_linked_user.socialaccount_set.get(provider="google")
    google_account.date_joined = timezone.now() - _td(days=30)
    google_account.save(update_fields=["date_joined"])

    ms_app = SocialApp.objects.create(
        provider="microsoft", name="MS", client_id="m", secret="s",
    )
    ms_app.sites.add(Site.objects.get_current())
    ms_account = SocialAccount.objects.create(
        user=google_linked_user, provider="microsoft", uid="ms-1",
    )
    SocialToken.objects.create(
        app=ms_app, account=ms_account,
        token="ms-tok", token_secret="ms-refresh",
        expires_at=timezone.now() + _td(hours=1),
    )

    provider, social, token = _get_social_token(google_linked_user)
    assert provider == "microsoft"
    assert token.token == "ms-tok"


@pytest.mark.django_db
def test_user_with_multiple_tokens_per_provider_uses_newest(google_linked_user):
    """When two SocialToken rows exist for the same account (different SocialApps,
    e.g. after a credentials-rotation re-registration), the newest one wins.

    Note: the DB enforces UNIQUE(app_id, account_id), so this only happens when
    there are multiple SocialApp rows for the same provider. We simulate that.
    """
    from allauth.socialaccount.models import SocialApp, SocialToken
    from django.contrib.sites.models import Site

    account = google_linked_user.socialaccount_set.get(provider="google")
    new_app = SocialApp.objects.create(
        provider="google", name="Google v2",
        client_id="rotated-client-id", secret="rotated-secret",
    )
    new_app.sites.add(Site.objects.get_current())

    newer = SocialToken.objects.create(
        app=new_app, account=account,
        token="newer-access", token_secret="newer-refresh",
        expires_at=timezone.now() + timedelta(hours=1),
    )

    _, _, returned = _get_social_token(google_linked_user)
    assert returned.id == newer.id
    assert returned.token == "newer-access"


# ---------------------------------------------------------------------------
# §6 — structured logging contract (no token leaks, correct outcome field)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_refresh_logs_outcome_rotated_when_refresh_token_changes(
    microsoft_linked_user, caplog
):
    import logging as _logging
    token = microsoft_linked_user.socialaccount_set.first().socialtoken_set.first()
    token.token_secret = "old-refresh"
    token.expires_at = timezone.now() - timedelta(minutes=5)
    token.save()

    fake_resp = MagicMock(status_code=200)
    fake_resp.json.return_value = {
        "access_token": "ms-access-new",
        "refresh_token": "ms-refresh-new",
        "expires_in": 3600,
    }

    caplog.set_level(_logging.INFO, logger="apps.mailing.engine")

    with patch("apps.mailing.engine.requests.post", return_value=fake_resp):
        _refresh_microsoft_token(token)

    rotated_records = [
        r for r in caplog.records
        if getattr(r, "outcome", None) == "rotated"
    ]
    assert len(rotated_records) == 1
    rec = rotated_records[0]
    assert rec.provider == "microsoft"
    assert rec.rotated is True
    # Token values must NOT appear anywhere in the structured payload.
    assert "ms-access-new" not in rec.getMessage()
    assert "ms-refresh-new" not in rec.getMessage()
    for value in vars(rec).values():
        s = str(value)
        assert "ms-access-new" not in s
        assert "ms-refresh-new" not in s


@pytest.mark.django_db
def test_refresh_logs_outcome_hit_cache_with_zero_latency(google_linked_user, caplog):
    import logging as _logging
    token = google_linked_user.socialaccount_set.first().socialtoken_set.first()
    token.expires_at = timezone.now() + timedelta(hours=1)
    token.save()

    caplog.set_level(_logging.INFO, logger="apps.mailing.engine")

    with patch("apps.mailing.engine.requests.post") as mock_post:
        _refresh_google_token(token)

    mock_post.assert_not_called()
    cache_records = [
        r for r in caplog.records
        if getattr(r, "outcome", None) == "hit_cache"
    ]
    assert len(cache_records) == 1
    assert cache_records[0].latency_ms == 0


@pytest.mark.django_db
def test_refresh_logs_outcome_terminal_error_on_invalid_grant(google_linked_user, caplog):
    import logging as _logging
    token = google_linked_user.socialaccount_set.first().socialtoken_set.first()
    token.token = "secret-access-DO-NOT-LEAK"
    token.token_secret = "secret-refresh-DO-NOT-LEAK"
    token.expires_at = timezone.now() - timedelta(minutes=5)
    token.save()

    fake_resp = MagicMock(status_code=400)
    fake_resp.json.return_value = {"error": "invalid_grant"}

    caplog.set_level(_logging.INFO, logger="apps.mailing.engine")

    with patch("apps.mailing.engine.requests.post", return_value=fake_resp):
        with pytest.raises(TokenExpiredError):
            _refresh_google_token(token)

    terminal_records = [
        r for r in caplog.records
        if getattr(r, "outcome", None) == "terminal_error"
    ]
    assert len(terminal_records) == 1
    rec = terminal_records[0]
    # No-leak assertion across every value in the structured payload.
    for value in vars(rec).values():
        s = str(value)
        assert "secret-access-DO-NOT-LEAK" not in s
        assert "secret-refresh-DO-NOT-LEAK" not in s


@pytest.mark.django_db
def test_refresh_logs_outcome_transient_error_with_no_token_leak(google_linked_user, caplog):
    """Spec scenario: 'Refresh failure logs outcome and never logs the token'
    explicitly enumerates both terminal_error and transient_error."""
    import logging as _logging
    token = google_linked_user.socialaccount_set.first().socialtoken_set.first()
    token.token = "transient-secret-access"
    token.token_secret = "transient-secret-refresh"
    token.expires_at = timezone.now() - timedelta(minutes=5)
    token.save()

    fake_resp = MagicMock(status_code=503)
    fake_resp.json.return_value = {"error": "backendError"}

    caplog.set_level(_logging.INFO, logger="apps.mailing.engine")

    with patch("apps.mailing.engine.requests.post", return_value=fake_resp):
        with pytest.raises(TokenRefreshTransientError):
            _refresh_google_token(token)

    transient_records = [
        r for r in caplog.records
        if getattr(r, "outcome", None) == "transient_error"
    ]
    assert len(transient_records) == 1
    rec = transient_records[0]
    assert rec.provider == "google"
    assert rec.rotated is False
    for value in vars(rec).values():
        s = str(value)
        assert "transient-secret-access" not in s
        assert "transient-secret-refresh" not in s


# ---------------------------------------------------------------------------
# Concurrency: select_for_update must serialize concurrent refreshes
# (proposal §1.3, design.md "concurrent refreshes are serialized" scenario)
# ---------------------------------------------------------------------------

@pytest.mark.django_db(transaction=True)
def test_concurrent_refresh_does_not_double_call_provider(google_linked_user):
    """Cache-fast-path: a back-to-back second call hits the in-memory cache
    (the first call mutated `token.expires_at` in-place), so only one HTTP
    refresh fires.
    """
    token = google_linked_user.socialaccount_set.first().socialtoken_set.first()
    token.expires_at = timezone.now() - timedelta(minutes=5)
    token.save()

    fake_resp = MagicMock(status_code=200)
    fake_resp.json.return_value = {"access_token": "race-winner", "expires_in": 3600}

    with patch("apps.mailing.engine.requests.post", return_value=fake_resp) as mock_post:
        _refresh_google_token(token)
        _refresh_google_token(token)

    assert mock_post.call_count == 1


@pytest.mark.django_db(transaction=True)
def test_locked_recheck_short_circuits_when_other_worker_already_refreshed(
    google_linked_user,
):
    """Worker B holds a stale in-memory token (expires_at in past) and so falls
    through the cheap pre-lock check and acquires the row lock. Between the time
    B's token was loaded and B acquired the lock, worker A already wrote a fresh
    expires_at to the DB. B must re-read under the lock, observe the freshness,
    and short-circuit WITHOUT issuing a duplicate refresh POST.
    """
    from allauth.socialaccount.models import SocialToken

    token = google_linked_user.socialaccount_set.first().socialtoken_set.first()
    token.expires_at = timezone.now() - timedelta(minutes=5)
    token.token = "old-access"
    token.save()

    # Simulate worker A completing the refresh by writing fresh values to the DB
    # directly. Note: the in-memory `token` object still shows the stale state.
    SocialToken.objects.filter(pk=token.pk).update(
        token="A-refreshed-this",
        expires_at=timezone.now() + timedelta(hours=1),
    )

    # B's in-memory token is still stale (`expires_at` in the past), so it
    # falls through the cheap check, acquires the lock, and re-reads.
    assert token.expires_at < timezone.now()

    with patch("apps.mailing.engine.requests.post") as mock_post:
        result = _refresh_google_token(token)

    # No HTTP call — B saw A's freshly persisted token under the lock.
    mock_post.assert_not_called()
    # B returned the value A had persisted, not its stale in-memory one.
    assert result == "A-refreshed-this"
