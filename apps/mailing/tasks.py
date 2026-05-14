"""
Celery tasks for the FastJob mailing engine.
- process_mailing_queue: runs every minute, sends one email per eligible active user.
- send_campaign_paused_notification: emails user when their campaign is paused.
"""
import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.db.models import Count, F, Q
from django.utils import timezone

from apps.companies.models import Blacklist
from apps.companies.queries import matching_companies_qs
from apps.mailing.engine import (
    QuotaExceededError,
    TokenExpiredError,
    TokenRefreshTransientError,
    send_cv_email,
)
from apps.mailing.models import EmailTemplate, MailingLog, SystemSettings

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=0)
def process_mailing_queue(self):
    """Process one email per active user, respecting slow-drip intervals."""
    lock_id = "lock_process_mailing_queue"
    # timeout is a safety measure in case the worker dies unexpectedly
    if not cache.add(lock_id, "true", 60 * 10):
        logger.info("process_mailing_queue is already running. Skipping tick.")
        return

    try:
        from apps.accounts.models import User

        cfg = SystemSettings.get()
        send_interval = timedelta(minutes=cfg.global_send_interval_minutes)
        cooldown = timedelta(hours=cfg.company_cooldown_hours)
        daily_limit = cfg.max_emails_per_day_per_user
        now = timezone.now()
        cooldown_threshold = now - cooldown
        day_threshold = now - timedelta(hours=24)

        active_users = User.objects.filter(
            is_campaign_active=True,
            active_cv__isnull=False,
        ).annotate(
            sent_last_24h=Count(
                "mailing_logs",
                filter=Q(
                    mailing_logs__status=MailingLog.Status.SENT,
                    mailing_logs__sent_at__gte=day_threshold,
                ),
            )
        )

        # Exclude blacklisted emails via subquery to avoid SQL length limits
        # as the blacklist grows.
        blacklist_subquery = Blacklist.objects.values("email")

        # Exclude companies contacted within the cooldown threshold via subquery.
        cooldown_subquery = MailingLog.objects.filter(
            sent_at__gte=cooldown_threshold,
            status=MailingLog.Status.SENT,
        ).values("company_id")

        # Tracking set for companies contacted DURING this specific task run (tick)
        # to prevent concurrent sends to the same company across different users
        # before the DB rows are committed and visible to the subquery.
        contacted_this_tick = set()

        for user in active_users:
            if not user.can_send():
                continue

            if user.sent_last_24h >= daily_limit:
                continue

            last_log = (
                MailingLog.objects.filter(user=user)
                .order_by("-sent_at")
                .first()
            )
            if last_log and (now - last_log.sent_at) < send_interval:
                continue

            companies = (
                matching_companies_qs(user.area_filters.all(), user.location_filters.all())
                .exclude(email__in=blacklist_subquery)
                .exclude(id__in=cooldown_subquery)
                .exclude(id__in=contacted_this_tick)
            )

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
                contacted_this_tick.add(company.id)
                logger.info("Sent CV: user_pk=%s → company_pk=%s", user.pk, company.pk)

            except TokenRefreshTransientError as exc:
                # Upstream blip (5xx, 429, network). Do not pause the campaign — the
                # next beat tick will retry naturally.
                log.status = MailingLog.Status.FAILED
                log.error_message = str(exc)
                log.save(update_fields=["status", "error_message"])
                logger.warning(
                    "Transient OAuth refresh error for user_pk=%s: %s", user.pk, exc
                )

            except TokenExpiredError as exc:
                log.status = MailingLog.Status.FAILED
                log.error_message = str(exc)
                log.save(update_fields=["status", "error_message"])
                user.is_campaign_active = False
                user.campaign_pause_reason = "expired"
                user.save(update_fields=["is_campaign_active", "campaign_pause_reason"])
                send_campaign_paused_notification.delay(user.pk, "expired")
                logger.warning("Token expired for user_pk=%s, campaign paused.", user.pk)

            except QuotaExceededError as exc:
                log.status = MailingLog.Status.FAILED
                log.error_message = str(exc)
                log.save(update_fields=["status", "error_message"])
                user.is_campaign_active = False
                user.campaign_pause_reason = "quota"
                user.save(update_fields=["is_campaign_active", "campaign_pause_reason"])
                send_campaign_paused_notification.delay(user.pk, "quota")
                logger.warning("Quota exceeded for user_pk=%s, campaign paused.", user.pk)

            except Exception as exc:
                log.status = MailingLog.Status.FAILED
                log.error_message = str(exc)
                log.save(update_fields=["status", "error_message"])
                logger.error("Send failed for user_pk=%s: %s", user.pk, exc)
    finally:
        cache.delete(lock_id)


@shared_task
def send_campaign_paused_notification(user_pk, reason):
    """Email the user explaining why their campaign was paused."""
    from apps.accounts.models import User

    try:
        user = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        return

    dashboard_url = f"{settings.SITE_SCHEME}://{settings.SITE_DOMAIN}/dashboard/"
    
    if reason == "quota":
        subject = "FastJob: Límite diario de tu proveedor alcanzado"
        message = (
            f"Hola {user.first_name or user.email},\n\n"
            "Tu proveedor de correo (Gmail/Outlook) ha alcanzado su límite diario de envíos. "
            "Tu campaña se ha pausado automáticamente para evitar bloqueos.\n\n"
            "No tienes que hacer nada. Tu campaña se reanudará mañana cuando el límite se restablezca.\n\n"
            f"Puedes ver el estado en tu panel: {dashboard_url}\n\n"
            "El equipo de FastJob"
        )
    elif reason == "expired":
        subject = "FastJob: Vuelve a conectar tu cuenta de correo"
        relink_url = f"{settings.SITE_SCHEME}://{settings.SITE_DOMAIN}/accounts/login/"
        message = (
            f"Hola {user.first_name or user.email},\n\n"
            "Tu sesión de correo ha expirado y tu campaña ha sido pausada.\n\n"
            f"Por favor, vuelve a iniciar sesión para reanudarla: {relink_url}\n\n"
            "El equipo de FastJob"
        )
    else:
        # Default fallback (unlinked or other)
        return

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )
