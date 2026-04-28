"""
Mailing engine: sends CVs via user-linked Google or Microsoft OAuth2 accounts.
Handles token refresh and raises TokenExpiredError when re-auth is needed.
"""
import base64
import logging
from datetime import timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class TokenExpiredError(Exception):
    pass


def _get_social_token(user):
    social = user.socialaccount_set.select_related().first()
    if not social:
        raise TokenExpiredError("No linked OAuth account found.")
    token = social.socialtoken_set.first()
    if not token:
        raise TokenExpiredError("No OAuth token found.")
    return social.provider, social, token


def _refresh_google_token(token):
    if token.expires_at and token.expires_at > timezone.now() + timedelta(seconds=60):
        return token.token

    provider_settings = settings.SOCIALACCOUNT_PROVIDERS.get("google", {})
    app_conf = provider_settings.get("APP", {})

    resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": app_conf.get("client_id"),
            "client_secret": app_conf.get("secret"),
            "refresh_token": token.token_secret,
            "grant_type": "refresh_token",
        },
        timeout=10,
    )

    if resp.status_code != 200:
        try:
            err = resp.json().get("error", "unknown")
        except ValueError:
            err = "unparseable"
        logger.error("Google token refresh failed: status=%d error=%s", resp.status_code, err)
        raise TokenExpiredError("Google token expired and could not be refreshed.")

    data = resp.json()
    token.token = data["access_token"]
    token.expires_at = timezone.now() + timedelta(seconds=data.get("expires_in", 3600))
    token.save(update_fields=["token", "expires_at"])
    return token.token


def _refresh_microsoft_token(token):
    if token.expires_at and token.expires_at > timezone.now() + timedelta(seconds=60):
        return token.token

    provider_settings = settings.SOCIALACCOUNT_PROVIDERS.get("microsoft", {})
    app_conf = provider_settings.get("APP", {})

    resp = requests.post(
        "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        data={
            "client_id": app_conf.get("client_id"),
            "client_secret": app_conf.get("secret"),
            "refresh_token": token.token_secret,
            "grant_type": "refresh_token",
            "scope": "Mail.Send User.Read offline_access",
        },
        timeout=10,
    )

    if resp.status_code != 200:
        try:
            err = resp.json().get("error", "unknown")
        except ValueError:
            err = "unparseable"
        logger.error("Microsoft token refresh failed: status=%d error=%s", resp.status_code, err)
        raise TokenExpiredError("Microsoft token expired and could not be refreshed.")

    data = resp.json()
    token.token = data["access_token"]
    token.expires_at = timezone.now() + timedelta(seconds=data.get("expires_in", 3600))
    token.save(update_fields=["token", "expires_at"])
    return token.token


def _send_via_gmail(access_token, from_email, to_email, subject, body_html):
    msg = MIMEMultipart("alternative")
    msg["To"] = to_email
    msg["From"] = from_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    resp = requests.post(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
        json={"raw": raw},
        timeout=15,
    )

    if resp.status_code not in (200, 202):
        raise Exception(f"Gmail API error {resp.status_code}: {resp.text}")


def _send_via_microsoft(access_token, to_email, subject, body_html):
    resp = requests.post(
        "https://graph.microsoft.com/v1.0/me/sendMail",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={
            "message": {
                "subject": subject,
                "body": {"contentType": "HTML", "content": body_html},
                "toRecipients": [{"emailAddress": {"address": to_email}}],
            },
            "saveToSentItems": False,
        },
        timeout=15,
    )

    if resp.status_code not in (200, 202):
        raise Exception(f"Microsoft Graph error {resp.status_code}: {resp.text}")


def send_cv_email(user, company, template, log):
    """
    Send a CV email from the user's linked OAuth account.
    Raises TokenExpiredError if the token cannot be refreshed.
    Raises Exception for other send failures.
    """
    base_url = f"{settings.SITE_SCHEME}://{settings.SITE_DOMAIN}"
    cv_url = f"{base_url}/cv/{log.cv_download_token}/"
    unsubscribe_url = f"{base_url}/unsubscribe/{log.unsubscribe_token}/"

    subject, body_html = template.render(
        company_name=company.name,
        cv_url=cv_url,
        unsubscribe_url=unsubscribe_url,
    )

    # Defence against header injection: a staff-authored template containing
    # `\r\nBcc: ...` in the subject would otherwise smuggle headers into Gmail's
    # MIME message. Microsoft Graph builds the subject as JSON, but stripping
    # here is uniform and cheap.
    subject = subject.replace("\r", "").replace("\n", "")

    provider, social, token = _get_social_token(user)

    if provider == "google":
        access_token = _refresh_google_token(token)
        from_email = user.email
        _send_via_gmail(access_token, from_email, company.email, subject, body_html)

    elif provider == "microsoft":
        access_token = _refresh_microsoft_token(token)
        _send_via_microsoft(access_token, company.email, subject, body_html)

    else:
        raise ValueError(f"Unsupported provider: {provider}")
