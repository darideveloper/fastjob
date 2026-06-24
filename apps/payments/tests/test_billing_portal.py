"""Tests for the Stripe Customer Portal view."""
from types import SimpleNamespace

import pytest
from django.urls import reverse

from apps.payments.models import CreditPackage, StripePayment


@pytest.mark.django_db
def test_billing_portal_requires_login(client):
    response = client.post(reverse("billing_portal"))
    assert response.status_code == 302
    assert "/accounts/login/" in response.url


@pytest.mark.django_db
def test_billing_portal_blocks_user_without_payments(client, user):
    client.force_login(user)
    response = client.post(reverse("billing_portal"))
    assert response.status_code == 302
    assert response.url == reverse("dashboard")


@pytest.mark.django_db
def test_billing_portal_blocks_when_stripe_has_no_customer(client, user, mocker):
    package = CreditPackage.objects.create(name="X", price_eur=5, credits=10)
    StripePayment.objects.create(
        user=user,
        package=package,
        stripe_session_id="cs_test_1",
        amount_eur=5,
        credits_granted=10,
        status=StripePayment.Status.COMPLETED,
    )
    client.force_login(user)
    mocker.patch("stripe.Customer.list", return_value=SimpleNamespace(data=[]))

    response = client.post(reverse("billing_portal"))
    assert response.status_code == 302
    assert response.url == reverse("dashboard")


@pytest.mark.django_db
def test_billing_portal_redirects_to_stripe_session(client, user, mocker):
    package = CreditPackage.objects.create(name="X", price_eur=5, credits=10)
    StripePayment.objects.create(
        user=user,
        package=package,
        stripe_session_id="cs_test_2",
        amount_eur=5,
        credits_granted=10,
        status=StripePayment.Status.COMPLETED,
    )
    client.force_login(user)
    customer = SimpleNamespace(id="cus_123")
    mocker.patch("stripe.Customer.list", return_value=SimpleNamespace(data=[customer]))
    session = SimpleNamespace(url="https://billing.stripe.com/session/xyz")
    mocker.patch("stripe.billing_portal.Session.create", return_value=session)

    response = client.post(reverse("billing_portal"))
    assert response.status_code == 302
    assert response.url == "https://billing.stripe.com/session/xyz"

    user.refresh_from_db()
    assert user.stripe_customer_id == "cus_123"


@pytest.mark.django_db
def test_billing_portal_uses_cached_customer_id(client, user, mocker):
    package = CreditPackage.objects.create(name="X", price_eur=5, credits=10)
    StripePayment.objects.create(
        user=user,
        package=package,
        stripe_session_id="cs_test_3",
        amount_eur=5,
        credits_granted=10,
        status=StripePayment.Status.COMPLETED,
    )
    user.stripe_customer_id = "cus_cached"
    user.save(update_fields=["stripe_customer_id"])
    client.force_login(user)

    # If the cache works, Customer.list should never be called.
    list_spy = mocker.patch("stripe.Customer.list")
    session_mock = mocker.patch(
        "stripe.billing_portal.Session.create",
        return_value=SimpleNamespace(url="https://billing.stripe.com/session/cached"),
    )

    response = client.post(reverse("billing_portal"))
    assert response.status_code == 302
    list_spy.assert_not_called()
    # Portal session was created with the cached ID.
    assert session_mock.call_args.kwargs["customer"] == "cus_cached"


@pytest.mark.django_db
def test_billing_portal_accepts_get_from_email_click(client, user, mocker):
    """An email client issues GET, not POST — the view must not 405."""
    package = CreditPackage.objects.create(name="X", price_eur=5, credits=10)
    StripePayment.objects.create(
        user=user,
        package=package,
        stripe_session_id="cs_test_get",
        amount_eur=5,
        credits_granted=10,
        status=StripePayment.Status.COMPLETED,
    )
    user.stripe_customer_id = "cus_get"
    user.save(update_fields=["stripe_customer_id"])
    client.force_login(user)
    mocker.patch(
        "stripe.billing_portal.Session.create",
        return_value=SimpleNamespace(url="https://billing.stripe.com/session/get"),
    )

    response = client.get(reverse("billing_portal"))
    assert response.status_code == 302
    assert response.url == "https://billing.stripe.com/session/get"
