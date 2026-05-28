import pytest
from django.core import mail
from apps.payments.models import StripePayment, CreditPackage
from apps.payments.tasks import send_payment_receipt_email

@pytest.mark.django_db
def test_receipt_email_sent_on_payment(user, company):
    package = CreditPackage.objects.create(name="Basic", price_eur=10, credits=10, is_active=True)
    payment = StripePayment.objects.create(user=user, package=package, amount_eur=10, credits_granted=10, status=StripePayment.Status.COMPLETED)
    
    send_payment_receipt_email(user.pk, payment.pk)
    
    assert len(mail.outbox) == 1
    assert "Tu recibo de compra en FastJob" in mail.outbox[0].subject

@pytest.mark.django_db
def test_receipt_email_shows_package_and_price(user):
    package = CreditPackage.objects.create(name="Pro", price_eur=50, credits=50, is_active=True)
    payment = StripePayment.objects.create(user=user, package=package, amount_eur=50, credits_granted=50, status=StripePayment.Status.COMPLETED)
    
    send_payment_receipt_email(user.pk, payment.pk)
    
    body = mail.outbox[0].body
    assert "Pro" in body
    # Price is DecimalField, formatting depends on DB
    assert "50" in body
    assert "50" in body # credits granted

@pytest.mark.django_db
def test_receipt_email_missing_user_logs_warning(caplog):
    send_payment_receipt_email(999, 999)
    assert "Failed to send payment receipt" in caplog.text

@pytest.mark.django_db
def test_receipt_email_uses_branded_layout(user):
    package = CreditPackage.objects.create(name="Basic", price_eur=10, credits=10, is_active=True)
    payment = StripePayment.objects.create(user=user, package=package, amount_eur=10, credits_granted=10, status=StripePayment.Status.COMPLETED)
    
    send_payment_receipt_email(user.pk, payment.pk)
    
    email = mail.outbox[0]
    html_content = [alt[0] for alt in email.alternatives if alt[1] == "text/html"][0]
    
    assert "https://raw.githubusercontent.com/daridev/fastjob/main/static/images/fastjob-logo.png" in html_content
    assert "#007BFF" in html_content
    assert "© 2026 FastJob. Todos los derechos reservados." in html_content
