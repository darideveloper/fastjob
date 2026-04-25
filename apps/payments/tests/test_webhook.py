"""
Tests for the Stripe webhook endpoint.

These verify that we:
  1. Reject requests with bad signatures (security).
  2. Grant credits exactly once on checkout.session.completed (idempotency).
  3. Don't crash on unknown event types (forward compatibility).
"""
from unittest.mock import patch

import pytest
import stripe
from django.urls import reverse

from apps.payments.models import CreditPackage, StripePayment


@pytest.fixture
def package(db):
    return CreditPackage.objects.create(
        name="Starter", price_eur=9.99, credits=50, is_active=True
    )


@pytest.fixture
def pending_payment(user, package):
    return StripePayment.objects.create(
        user=user,
        package=package,
        stripe_session_id="cs_test_123",
        amount_eur=9.99,
        credits_granted=50,
        status=StripePayment.Status.PENDING,
    )


@pytest.mark.django_db
def test_webhook_rejects_invalid_signature(client):
    with patch("stripe.Webhook.construct_event", side_effect=stripe.error.SignatureVerificationError("bad", "sig")):
        resp = client.post(
            reverse("stripe_webhook"),
            data=b"{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="invalid",
        )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_webhook_grants_credits_on_successful_checkout(client, user, pending_payment):
    starting_credits = user.credits_remaining

    fake_event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": pending_payment.stripe_session_id,
                "payment_intent": "pi_test_456",
            }
        },
    }
    with patch("stripe.Webhook.construct_event", return_value=fake_event):
        resp = client.post(
            reverse("stripe_webhook"),
            data=b"{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="valid",
        )

    assert resp.status_code == 200
    user.refresh_from_db()
    pending_payment.refresh_from_db()
    assert user.credits_remaining == starting_credits + pending_payment.credits_granted
    assert pending_payment.status == StripePayment.Status.COMPLETED
    assert pending_payment.stripe_payment_intent == "pi_test_456"


@pytest.mark.django_db
def test_webhook_does_not_double_credit_on_replay(client, user, pending_payment):
    """Stripe retries webhooks on 5xx. We must be idempotent."""
    fake_event = {
        "type": "checkout.session.completed",
        "data": {"object": {"id": pending_payment.stripe_session_id, "payment_intent": "pi_1"}},
    }
    with patch("stripe.Webhook.construct_event", return_value=fake_event):
        client.post(reverse("stripe_webhook"), data=b"{}", content_type="application/json",
                    HTTP_STRIPE_SIGNATURE="v")
        # Same event replayed.
        client.post(reverse("stripe_webhook"), data=b"{}", content_type="application/json",
                    HTTP_STRIPE_SIGNATURE="v")

    user.refresh_from_db()
    assert user.credits_remaining == 10 + pending_payment.credits_granted  # only once


@pytest.mark.django_db
def test_webhook_ignores_unknown_event_types(client):
    fake_event = {"type": "payment_intent.created", "data": {"object": {}}}
    with patch("stripe.Webhook.construct_event", return_value=fake_event):
        resp = client.post(
            reverse("stripe_webhook"), data=b"{}",
            content_type="application/json", HTTP_STRIPE_SIGNATURE="v",
        )
    assert resp.status_code == 200


@pytest.mark.django_db
def test_webhook_credit_increment_uses_atomic_update(client, user, package):
    """C1 race-fix proof: simulate two distinct sessions completing while a
    stale `user` object is held in memory. Each grant must compose at the
    DB level, not overwrite the prior value."""
    p1 = StripePayment.objects.create(
        user=user, package=package, stripe_session_id="cs_a",
        amount_eur=9.99, credits_granted=3, status=StripePayment.Status.PENDING,
    )
    p2 = StripePayment.objects.create(
        user=user, package=package, stripe_session_id="cs_b",
        amount_eur=9.99, credits_granted=4, status=StripePayment.Status.PENDING,
    )
    starting = user.credits_remaining  # 10 from the conftest fixture

    for sess_id, intent in [("cs_a", "pi_a"), ("cs_b", "pi_b")]:
        fake_event = {
            "type": "checkout.session.completed",
            "data": {"object": {"id": sess_id, "payment_intent": intent}},
        }
        with patch("stripe.Webhook.construct_event", return_value=fake_event):
            client.post(reverse("stripe_webhook"), data=b"{}",
                        content_type="application/json", HTTP_STRIPE_SIGNATURE="v")

    user.refresh_from_db()
    # Both grants composed: starting (10) + 3 + 4 = 17
    assert user.credits_remaining == starting + 3 + 4
