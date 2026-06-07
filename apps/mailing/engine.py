"""
Mailing engine: sends CVs via user-linked Google or Microsoft OAuth2 accounts.

Three failure modes are surfaced to callers:

- ``TokenExpiredError``  — terminal: the refresh token is dead (revoked, expired,
  scope mismatch). The worker pauses the campaign and asks the user to re-link.
- ``TokenRefreshTransientError`` — retryable: upstream outage, rate limit, or
  network blip. The worker should log + skip this user-tick without pausing.
- ``CVFileMissingError`` — terminal: the active CV file cannot be read from
  storage. The worker pauses the campaign and asks the user to re-upload.

Refresh requests persist any rotated ``refresh_token`` returned by the provider
(Microsoft rotates on every call; Google rotates rarely). The refresh+save block
is serialized via ``select_for_update`` so two concurrent workers cannot clobber
each other's rotated value.
"""
import base64
import logging
import time
from datetime import timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

import requests
from allauth.socialaccount.models import SocialApp, SocialToken
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.mailing.email import render_branded_email

logger = logging.getLogger(__name__)


# Process-level latch: the Microsoft Graph "unprefixed List-Unsubscribe rejected"
# fallback emits exactly one WARNING per worker process, regardless of how many
# subsequent sends take the same fallback path. Without this gate every send
# floods the log when a tenant persistently rejects the unprefixed header.
_graph_fallback_warned = False


class TokenExpiredError(Exception):
    """Refresh failed for a reason the user must act on (re-link required)."""


class TokenRefreshTransientError(Exception):
    """Refresh failed for a reason that will likely succeed on the next tick."""


class QuotaExceededError(Exception):
    """Provider-enforced daily sending limit reached."""


class CVFileMissingError(Exception):
    """The user's active CV file could not be read from storage."""


# OAuth-protocol error codes that mean "the refresh token itself is dead."
# Anything else returned with a 4xx is treated conservatively as terminal too;
# only HTTP 5xx / 429 / network errors are classified as transient.
_TERMINAL_OAUTH_ERRORS = frozenset(
    {"invalid_grant", "invalid_client", "unauthorized_client"}
)


def _classify_refresh_failure(resp_or_exc):
    """Map a failed refresh response or raised exception to the right exception
    instance. Returns the exception (caller raises it) so the call sites stay
    one-liners.
    """
    if isinstance(resp_or_exc, (requests.Timeout, requests.ConnectionError)):
        return TokenRefreshTransientError(f"network error: {resp_or_exc.__class__.__name__}")

    resp = resp_or_exc
    status = getattr(resp, "status_code", None)

    if status == 429 or (status is not None and 500 <= status < 600):
        return TokenRefreshTransientError(f"upstream {status}")

    # 4xx with a recognized OAuth-protocol error → terminal.
    try:
        err = resp.json().get("error", "unknown") if resp is not None else "unknown"
    except ValueError:
        err = "unparseable"

    if status in (401, 403) or err in _TERMINAL_OAUTH_ERRORS:
        return TokenExpiredError(f"refresh denied: status={status} error={err}")

    # Unknown 4xx — be conservative and treat as terminal so users get notified.
    return TokenExpiredError(f"refresh failed: status={status} error={err}")


def _get_social_token(user):
    """Return ``(provider, social_account, social_token)`` for the user.

    Selection rule: when a user has linked more than one provider, the most
    recently linked ``SocialAccount`` (by ``date_joined`` descending) wins. For
    that account, the most recently saved ``SocialToken`` (by ``id`` descending)
    is returned. Both orderings are explicit so we never inherit the database's
    default row order — that has bitten us before with non-deterministic test
    flakes and surprise provider switches.
    """
    social = user.socialaccount_set.order_by("-date_joined").first()
    if not social:
        raise TokenExpiredError("No linked OAuth account found.")
    token = social.socialtoken_set.order_by("-id").first()
    if not token:
        raise TokenExpiredError("No OAuth token found.")
    return social.provider, social, token


def _log_refresh(provider, user_pk, outcome, latency_ms, rotated):
    """Emit exactly one structured log record per refresh attempt.

    Token values are never logged — only the metadata operators need to detect
    rotation regressions and transient-error spikes.
    """
    logger.info(
        "oauth_refresh provider=%s user_pk=%s outcome=%s latency_ms=%s rotated=%s",
        provider, user_pk, outcome, latency_ms, rotated,
        extra={
            "provider": provider,
            "user_pk": user_pk,
            "outcome": outcome,
            "latency_ms": latency_ms,
            "rotated": rotated,
        },
    )


def _user_pk_for_token(token):
    try:
        return token.account.user_id
    except Exception:
        return None


def _refresh_token_locked(token, provider, post_url, post_data, post_extra=None):
    """Common refresh path: lock row, double-check expiry, POST, persist rotation.

    Returns the (possibly cached) access token string. Raises
    ``TokenExpiredError`` or ``TokenRefreshTransientError`` per the classifier.
    """
    user_pk = _user_pk_for_token(token)

    # Cheap path: if the in-memory copy still has comfortable runway, skip the
    # lock entirely. Saves both a row lock and an HTTP round-trip.
    if token.expires_at and token.expires_at > timezone.now() + timedelta(seconds=600):
        _log_refresh(provider, user_pk, "hit_cache", 0, False)
        return token.token

    with transaction.atomic():
        # Re-read under FOR UPDATE so two workers cannot both refresh and clobber
        # each other's rotated refresh_token.
        locked = SocialToken.objects.select_for_update().get(pk=token.pk)

        if locked.expires_at and locked.expires_at > timezone.now() + timedelta(seconds=600):
            # Another worker refreshed this row while we were waiting on the lock.
            token.token = locked.token
            token.token_secret = locked.token_secret
            token.expires_at = locked.expires_at
            _log_refresh(provider, user_pk, "hit_cache", 0, False)
            return locked.token

        t0 = time.monotonic()
        try:
            resp = requests.post(post_url, data=post_data, timeout=10, **(post_extra or {}))
        except (requests.Timeout, requests.ConnectionError) as exc:
            latency_ms = int((time.monotonic() - t0) * 1000)
            _log_refresh(provider, user_pk, "transient_error", latency_ms, False)
            raise _classify_refresh_failure(exc) from exc

        latency_ms = int((time.monotonic() - t0) * 1000)

        if resp.status_code != 200:
            classified = _classify_refresh_failure(resp)
            outcome = (
                "transient_error"
                if isinstance(classified, TokenRefreshTransientError)
                else "terminal_error"
            )
            try:
                err = resp.json().get("error", "unknown")
            except ValueError:
                err = "unparseable"
            logger.error(
                "%s token refresh failed: status=%d error=%s",
                provider.capitalize(), resp.status_code, err,
            )
            _log_refresh(provider, user_pk, outcome, latency_ms, False)
            raise classified

        data = resp.json()
        rotated = "refresh_token" in data and data["refresh_token"] != locked.token_secret

        locked.token = data["access_token"]
        locked.expires_at = timezone.now() + timedelta(seconds=data.get("expires_in", 3600))
        update_fields = ["token", "expires_at"]
        if "refresh_token" in data:
            locked.token_secret = data["refresh_token"]
            update_fields.append("token_secret")
        locked.save(update_fields=update_fields)

        # Mirror the freshly persisted state onto the caller's in-memory token
        # so subsequent reads (e.g. send-time diagnostics) stay consistent.
        token.token = locked.token
        token.token_secret = locked.token_secret
        token.expires_at = locked.expires_at

        _log_refresh(
            provider, user_pk,
            "rotated" if rotated else "refreshed",
            latency_ms, rotated,
        )
        return locked.token


def _get_social_app(provider):
    app = SocialApp.objects.filter(provider=provider).first()
    if not app:
        raise TokenExpiredError(f"SocialApp configuration missing for {provider}.")
    return app.client_id, app.secret


def _refresh_google_token(token):
    client_id, secret = _get_social_app("google")
    return _refresh_token_locked(
        token,
        provider="google",
        post_url="https://oauth2.googleapis.com/token",
        post_data={
            "client_id": client_id,
            "client_secret": secret,
            "refresh_token": token.token_secret,
            "grant_type": "refresh_token",
        },
    )


def _refresh_microsoft_token(token):
    client_id, secret = _get_social_app("microsoft")
    tenant = getattr(settings, "MICROSOFT_TENANT", "common") or "common"
    return _refresh_token_locked(
        token,
        provider="microsoft",
        post_url=f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
        post_data={
            "client_id": client_id,
            "client_secret": secret,
            "refresh_token": token.token_secret,
            "grant_type": "refresh_token",
            "scope": "Mail.Send User.Read offline_access",
        },
    )


def _send_via_gmail(access_token, from_email, to_email, subject, body_html, attachment, unsubscribe_url=None):
    msg = MIMEMultipart("mixed")
    msg["To"] = to_email
    msg["From"] = from_email
    msg["Subject"] = subject
    if unsubscribe_url:
        msg["List-Unsubscribe"] = f"<{unsubscribe_url}>"
        msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
    
    # Body
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    # Attachment
    if attachment:
        attachment_part = MIMEApplication(attachment["content"], _subtype="pdf", Name=attachment["name"])
        attachment_part['Content-Disposition'] = f'attachment; filename="{attachment["name"]}"'
        msg.attach(attachment_part)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    resp = requests.post(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
        json={"raw": raw},
        timeout=15,
    )

    if resp.status_code not in (200, 202):
        if "rateLimitExceeded" in resp.text or "userRateLimitExceeded" in resp.text or "(Mail sending)" in resp.text:
            raise QuotaExceededError(f"Gmail quota exceeded: {resp.text}")

        if resp.status_code in (401, 403):
            raise TokenExpiredError(f"Gmail API auth error {resp.status_code}: {resp.text}")
        if resp.status_code == 429 or 500 <= resp.status_code < 600:
            raise TokenRefreshTransientError(f"Gmail API transient error {resp.status_code}: {resp.text}")
        raise Exception(f"Gmail API error {resp.status_code}: {resp.text}")


def _send_via_microsoft(access_token, to_email, subject, body_html, attachment, unsubscribe_url=None):
    message = {
        "subject": subject,
        "body": {"contentType": "HTML", "content": body_html},
        "toRecipients": [{"emailAddress": {"address": to_email}}],
    }
    
    if attachment:
        message["attachments"] = [
            {
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": attachment["name"],
                "contentType": attachment["content_type"],
                "contentBytes": base64.b64encode(attachment["content"]).decode("utf-8")
            }
        ]

    if unsubscribe_url:
        message["internetMessageHeaders"] = [
            {"name": "List-Unsubscribe", "value": f"<{unsubscribe_url}>"},
            {"name": "List-Unsubscribe-Post", "value": "List-Unsubscribe=One-Click"},
        ]

    resp = requests.post(
        "https://graph.microsoft.com/v1.0/me/sendMail",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={"message": message, "saveToSentItems": True},
        timeout=15,
    )

    if resp.status_code == 400 and unsubscribe_url:
        # Fallback: some tenant configurations reject unprefixed header names.
        # The retry must happen on every fallback, but the WARNING is gated to
        # once-per-process so persistent-fallback tenants don't flood the log.
        global _graph_fallback_warned
        if not _graph_fallback_warned:
            logger.warning(
                "Graph rejected List-Unsubscribe headers; retrying with x- prefix",
                extra={
                    "provider": "microsoft",
                    "status": resp.status_code,
                    "fallback": "x-prefix",
                },
            )
            _graph_fallback_warned = True
        for hdr in message.get("internetMessageHeaders", []):
            hdr["name"] = "x-" + hdr["name"].lower()
        resp = requests.post(
            "https://graph.microsoft.com/v1.0/me/sendMail",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={"message": message, "saveToSentItems": True},
            timeout=15,
        )

    if resp.status_code not in (200, 202):
        if "ErrorExceededMessageLimit" in resp.text:
            raise QuotaExceededError(f"Microsoft quota exceeded: {resp.text}")

        if resp.status_code in (401, 403):
            raise TokenExpiredError(f"Microsoft Graph auth error {resp.status_code}: {resp.text}")
        if resp.status_code == 429 or 500 <= resp.status_code < 600:
            raise TokenRefreshTransientError(f"Microsoft Graph transient error {resp.status_code}: {resp.text}")
        raise Exception(f"Microsoft Graph error {resp.status_code}: {resp.text}")


def send_cv_email(user, company, template, log):
    """
    Send a CV email from the user's linked OAuth account.
    Raises TokenExpiredError if the token cannot be refreshed.
    Raises Exception for other send failures.
    """
    base_url = f"{settings.SITE_SCHEME}://{settings.SITE_DOMAIN}"
    unsubscribe_url = f"{base_url}/unsubscribe/{log.unsubscribe_token}/"

    subject, body_html = template.render(
        company_name=company.name,
        unsubscribe_url=unsubscribe_url,
    )

    body_html = render_branded_email(subject, body_html)


    # Defence against header injection: a staff-authored template containing
    # `\r\nBcc: ...` in the subject would otherwise smuggle headers into Gmail's
    # MIME message. Microsoft Graph builds the subject as JSON, but stripping
    # here is uniform and cheap.
    subject = subject.replace("\r", "").replace("\n", "")
    
    try:
        if not user.active_cv or not user.active_cv.file:
            raise ValueError("No active CV file associated with the user.")
        cv_file = user.active_cv.file
        with cv_file.open("rb") as f:
            attachment_content = f.read()
        attachment = {
            "name": cv_file.name.rsplit('/', 1)[-1],
            "content": attachment_content,
            "content_type": "application/pdf"
        }
    except (OSError, FileNotFoundError, ValueError, AttributeError) as e:
        raise CVFileMissingError(f"Failed to read CV file: {e}")

    provider, social, token = _get_social_token(user)

    if provider == "google":
        access_token = _refresh_google_token(token)
        from_email = user.email
        _send_via_gmail(access_token, from_email, company.email, subject, body_html, attachment, unsubscribe_url)

    elif provider == "microsoft":
        access_token = _refresh_microsoft_token(token)
        _send_via_microsoft(access_token, company.email, subject, body_html, attachment, unsubscribe_url)

    else:
        raise ValueError(f"Unsupported provider: {provider}")
