import logging

from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django_ratelimit.decorators import ratelimit

from apps.companies.models import Blacklist
from .models import MailingLog

logger = logging.getLogger(__name__)


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
        return redirect(url)
    except Exception:
        return render(request, "mailing/cv_not_found.html", status=500)


# Unsubscribe should effectively be single-use per link; 10/hour is defensive.
@ratelimit(key="ip", rate="10/h", block=True)
def unsubscribe(request, token):
    """
    Adds the company email to the Blacklist when they click the unsubscribe link.
    """
    log = get_object_or_404(MailingLog, unsubscribe_token=token)

    email = log.company_email_snapshot or (log.company.email if log.company else None)
    if not email:
        raise Http404

    Blacklist.objects.get_or_create(
        email=email,
        defaults={"reason": "unsubscribe", "added_at": timezone.now()},
    )

    return render(request, "mailing/unsubscribe.html", {"email": email})
