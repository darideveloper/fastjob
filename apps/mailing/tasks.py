"""
Celery tasks for the ResumeLink mailing engine.
- process_mailing_queue: runs every minute, sends one email per eligible active user.
- send_relink_notification: emails user when their OAuth token has expired.
"""
import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import F
from django.utils import timezone

from apps.companies.models import Blacklist, Company
from apps.mailing.engine import TokenExpiredError, send_cv_email
from apps.mailing.models import EmailTemplate, MailingLog, SystemSettings

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=0)
def process_mailing_queue(self):
    """Process one email per active user, respecting slow-drip intervals."""
    from apps.accounts.models import User

    cfg = SystemSettings.get()
    send_interval = timedelta(minutes=cfg.global_send_interval_minutes)
    cooldown = timedelta(hours=cfg.company_cooldown_hours)
    now = timezone.now()
    cooldown_threshold = now - cooldown

    active_users = User.objects.filter(
        is_campaign_active=True,
        credits_remaining__gt=0,
        active_cv__isnull=False,
    )

    blacklisted_emails = set(Blacklist.objects.values_list("email", flat=True))
    recently_contacted_ids = set(
        MailingLog.objects.filter(
            sent_at__gte=cooldown_threshold,
            status=MailingLog.Status.SENT,
        ).values_list("company_id", flat=True)
    )

    for user in active_users:
        last_log = (
            MailingLog.objects.filter(user=user, status=MailingLog.Status.SENT)
            .order_by("-sent_at")
            .first()
        )
        if last_log and (now - last_log.sent_at) < send_interval:
            continue

        companies = Company.objects.exclude(email__in=blacklisted_emails).exclude(
            id__in=recently_contacted_ids
        )

        if user.area_filter:
            companies = companies.filter(area__icontains=user.area_filter)
        if user.location_filter:
            companies = companies.filter(location__icontains=user.location_filter)

        company = companies.order_by("?").first()
        if not company:
            logger.info("No eligible companies for user_pk=%s", user.pk)
            continue

        template = EmailTemplate.objects.filter(is_active=True).order_by("?").first()
        if not template:
            logger.warning("No active email templates found.")
            continue

        log = MailingLog.objects.create(
            user=user,
            company=company,
            email_template=template,
            cv=user.active_cv,
            status=MailingLog.Status.SENT,
        )

        try:
            send_cv_email(user, company, template, log)
            # Atomic decrement: avoids the lost-update race window between
            # concurrent workers reading the same credits_remaining value.
            User.objects.filter(pk=user.pk).update(
                credits_remaining=F("credits_remaining") - 1
            )
            user.refresh_from_db(fields=["credits_remaining"])
            company.last_received_at = now
            company.save(update_fields=["last_received_at"])
            recently_contacted_ids.add(company.id)
            logger.info("Sent CV: user_pk=%s → company_pk=%s", user.pk, company.pk)

        except TokenExpiredError as exc:
            log.status = MailingLog.Status.FAILED
            log.error_message = str(exc)
            log.save(update_fields=["status", "error_message"])
            user.is_campaign_active = False
            user.save(update_fields=["is_campaign_active"])
            send_relink_notification.delay(user.pk)
            logger.warning("Token expired for user_pk=%s, campaign paused.", user.pk)

        except Exception as exc:
            log.status = MailingLog.Status.FAILED
            log.error_message = str(exc)
            log.save(update_fields=["status", "error_message"])
            logger.error("Send failed for user_pk=%s: %s", user.pk, exc)


@shared_task
def send_relink_notification(user_pk):
    """Email the user asking them to re-authorize their OAuth account."""
    from apps.accounts.models import User

    try:
        user = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        return

    scheme = "https" if not settings.DEBUG else "http"
    relink_url = f"{scheme}://{settings.SITE_DOMAIN}/accounts/login/"

    send_mail(
        subject="ResumeLink: Vuelve a conectar tu cuenta de correo",
        message=(
            f"Hola {user.first_name or user.email},\n\n"
            "Tu sesión de correo ha expirado y tu campaña ha sido pausada.\n\n"
            f"Por favor, vuelve a iniciar sesión para reanudarla: {relink_url}\n\n"
            "El equipo de ResumeLink"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )
