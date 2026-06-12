import logging
from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from apps.accounts.models import User
from apps.payments.models import StripePayment
from apps.mailing.email import render_branded_email

logger = logging.getLogger(__name__)

@shared_task
def send_payment_receipt_email(user_pk, payment_pk):
    try:
        user = User.objects.get(pk=user_pk)
        payment = StripePayment.objects.get(pk=payment_pk)
    except (User.DoesNotExist, StripePayment.DoesNotExist) as e:
        logger.warning("Failed to send payment receipt for user_pk=%s, payment_pk=%s: %s", user_pk, payment_pk, e)
        return

    dashboard_url = f"{settings.SITE_SCHEME}://{settings.SITE_DOMAIN}/dashboard/"
    billing_url = f"{settings.SITE_SCHEME}://{settings.SITE_DOMAIN}/payments/billing/"
    
    context = {
        "user": user,
        "payment": payment,
        "package": payment.package,
        "dashboard_url": dashboard_url,
        "billing_url": billing_url,
    }
    subject = "Tu recibo de compra en FastJob"
    body_html = render_branded_email(
        subject=subject,
        body_html=render_to_string("email/payment_receipt.html", context),
        context=context
    )
    body_text = render_to_string("email/payment_receipt.txt", context)

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
        logger.error("Failed to send payment receipt email to user_pk=%s: %s", user_pk, e, exc_info=True)
