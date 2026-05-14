import pytest
from unittest.mock import patch
from django.urls import reverse
from apps.payments.models import CreditPackage, StripePayment
from apps.accounts.models import User

@pytest.fixture
def package(db):
    return CreditPackage.objects.create(
        name="Starter", price_eur=9.99, credits=50, is_active=True
    )

@pytest.mark.django_db
def test_webhook_forgives_negative_balance(client, user, package):
    # Set user to negative balance
    user.credits_remaining = -5
    user.total_purchased_credits = 50 # already bought 50, now using margin
    user.save()

    pending_payment = StripePayment.objects.create(
        user=user,
        package=package,
        stripe_session_id="cs_test_forgive",
        amount_eur=9.99,
        credits_granted=50,
        status=StripePayment.Status.PENDING,
    )

    fake_event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": pending_payment.stripe_session_id,
                "payment_intent": "pi_test_forgive",
            }
        },
    }
    with patch("stripe.Webhook.construct_event", return_value=fake_event):
        client.post(
            reverse("stripe_webhook"),
            data=b"{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="valid",
        )

    user.refresh_from_db()
    # Should be exactly 50 (purchased 50, -5 debt forgiven)
    assert user.credits_remaining == 50
    # total_purchased_credits should be 100 (50 old + 50 new)
    assert user.total_purchased_credits == 100

@pytest.mark.django_db
def test_webhook_increments_positive_balance_normally(client, user, package):
    # Set user to positive balance
    user.credits_remaining = 10
    user.total_purchased_credits = 50
    user.save()

    pending_payment = StripePayment.objects.create(
        user=user,
        package=package,
        stripe_session_id="cs_test_positive",
        amount_eur=9.99,
        credits_granted=50,
        status=StripePayment.Status.PENDING,
    )

    fake_event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": pending_payment.stripe_session_id,
                "payment_intent": "pi_test_positive",
            }
        },
    }
    with patch("stripe.Webhook.construct_event", return_value=fake_event):
        client.post(
            reverse("stripe_webhook"),
            data=b"{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="valid",
        )

    user.refresh_from_db()
    # 10 + 50 = 60
    assert user.credits_remaining == 60
    assert user.total_purchased_credits == 100
