import hashlib
import logging

from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit

from apps.companies.models import Blacklist
from .models import MailingLog

logger = logging.getLogger(__name__)


def _mask_email(email):
    """Return a privacy-safe display version: foo@bar.com → f**@bar.com."""
    local, _, domain = email.partition("@")
    if len(local) <= 1:
        masked_local = local
    else:
        masked_local = local[0] + "**"
    return f"{masked_local}@{domain}"


# 30 req/hour/IP is generous for a legitimate recipient (typically 1-3 clicks
# per email); anything higher signals abuse / scraping. block=True raises
# Ratelimited, which our middleware converts to a 429.
@ratelimit(key="ip", rate="30/h", block=True)
def cv_download(request, token):
    """
    Validates the cv_download_token and redirects to a time-limited
    pre-signed S3/Spaces URL so the company can download the CV.
    """
    log = get_object_or_404(MailingLog, cv_download_token=token)

    # Block access if the recipient has opted out.
    email = (log.company_email_snapshot or (log.company.email if log.company else "")).lower()
    if email and Blacklist.objects.filter(email=email).exists():
        return render(request, "mailing/cv_revoked.html", status=410)

    # Prefer the CV snapshot at send time; fall back to the user's current
    # active CV for legacy logs that predate the cv FK on MailingLog.
    cv = log.cv or log.user.active_cv
    if not cv or not cv.file:
        return render(request, "mailing/cv_not_found.html", status=404)

    try:
        import boto3
        from botocore.client import Config

        s3 = boto3.client(
            "s3",
            region_name=settings.AWS_S3_REGION_NAME,
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            config=Config(signature_version="s3v4"),
        )
        url = s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.AWS_STORAGE_BUCKET_NAME,
                "Key": cv.file.name,
            },
            ExpiresIn=settings.AWS_QUERYSTRING_EXPIRE,
        )
        # H13: presigned URL contains a time-bounded signature. Caching the
        # 302 (in a CDN, browser, or corporate proxy) would let someone
        # who replays the cached redirect fetch the CV after the link's
        # cv_download_token has been revoked or its rate-limit hit.
        response = redirect(url)
        response["Cache-Control"] = "no-store"
        return response
    except Exception:
        return render(request, "mailing/cv_not_found.html", status=500)


# Unsubscribe should effectively be single-use per link; 10/hour is defensive.
# @csrf_exempt: the unsubscribe token in the URL is the auth factor (UUID4,
# unique-indexed, known only to the original email recipient). Standard Django
# CSRF cannot be used here because the recipient has no session or CSRF cookie.
# This matches the security model of password-reset links and S3 presigned URLs.
@csrf_exempt  # noqa: S003 — UUID token in URL is the auth factor; see design.md §2
@require_http_methods(["GET", "POST"])
@ratelimit(key="ip", rate="10/h", block=True)
def unsubscribe(request, token):
    log = get_object_or_404(MailingLog, unsubscribe_token=token)

    email = log.company_email_snapshot or (log.company.email if log.company else None)
    if not email:
        raise Http404

    if request.method == "GET":
        return render(request, "mailing/unsubscribe_confirm.html", {
            "masked_email": _mask_email(email),
        })

    # POST: commit the unsubscribe.
    Blacklist.add(email)

    if not log.unsubscribed_at:
        log.unsubscribed_at = timezone.now()
        log.save(update_fields=["unsubscribed_at"])

    logger.info(
        "unsubscribed",
        extra={
            "outcome": "unsubscribed",
            "user_pk": log.user_id,
            "template_id": log.email_template_id,
            "log_pk": log.pk,
            "company_email_sha256": hashlib.sha256(email.strip().lower().encode()).hexdigest(),
        },
    )

    return render(request, "mailing/unsubscribe.html", {"email": email})
