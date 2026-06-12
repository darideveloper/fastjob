import logging
from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from apps.accounts.models import User
from apps.mailing.email import render_branded_email

logger = logging.getLogger(__name__)

@shared_task
def send_welcome_email(user_pk):
    try:
        user = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        return

    dashboard_url = f"{settings.SITE_SCHEME}://{settings.SITE_DOMAIN}/dashboard/"
    oauth_url = f"{settings.SITE_SCHEME}://{settings.SITE_DOMAIN}/accounts/login/"
    context = {
        "user": user,
        "dashboard_url": dashboard_url,
        "oauth_url": oauth_url,
    }
    subject = "Bienvenido a FastJob"
    body_html = render_branded_email(
        subject=subject,
        body_html=render_to_string("email/welcome.html", context),
        context=context
    )
    body_text = render_to_string("email/welcome.txt", context)

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=body_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        msg.attach_alternative(body_html, "text/html")
        msg.send()
    except Exception as e:
        logger.error("Failed to send welcome email to user_pk=%s: %s", user_pk, e, exc_info=True)


@shared_task
def send_account_deleted_email(user_email):
    home_url = f"{settings.SITE_SCHEME}://{settings.SITE_DOMAIN}/"
    context = {"home_url": home_url}
    subject = "FastJob: Tu cuenta ha sido eliminada"
    
    body_html = render_branded_email(
        subject=subject,
        body_html=render_to_string("email/account_deleted.html", context),
        context=context
    )
    body_text = render_to_string("email/account_deleted.txt", context)

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=body_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user_email],
        )
        msg.attach_alternative(body_html, "text/html")
        msg.send()
    except Exception as e:
        logger.error("Failed to send account deleted email to %s: %s", user_email, e, exc_info=True)


@shared_task
def send_oauth_link_email(user_pk, provider_name):
    from apps.accounts.models import User
    try:
        user = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        return

    dashboard_url = f"{settings.SITE_SCHEME}://{settings.SITE_DOMAIN}/dashboard/"
    context = {"provider": provider_name, "dashboard_url": dashboard_url}
    subject = f"FastJob: Nueva cuenta de {provider_name} vinculada"
    
    body_html = render_branded_email(
        subject=subject,
        body_html=render_to_string("email/oauth_linked.html", context),
        context=context
    )
    body_text = render_to_string("email/oauth_linked.txt", context)

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=body_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        msg.attach_alternative(body_html, "text/html")
        msg.send()
    except Exception as e:
        logger.error("Failed to send OAuth link email to user_pk=%s: %s", user_pk, e, exc_info=True)
