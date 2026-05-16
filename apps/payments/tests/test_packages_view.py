import pytest
from django.urls import reverse

from apps.mailing.models import MailingLog
from apps.payments.models import CreditPackage


@pytest.fixture
def package(db):
    return CreditPackage.objects.create(
        name="Starter", price_eur=9.99, credits=50, is_active=True
    )


@pytest.mark.django_db
def test_packages_context_includes_successful_sends_count(client, user, package, company, email_template):
    MailingLog.objects.create(
        user=user,
        company=company,
        email_template=email_template,
        status=MailingLog.Status.SENT,
    )
    MailingLog.objects.create(
        user=user,
        company=company,
        email_template=email_template,
        status=MailingLog.Status.SENT,
    )

    client.force_login(user)
    response = client.get(reverse("payment_packages"))

    assert response.status_code == 200
    count = response.context["successful_sends_count"]
    assert count >= 0
    assert count == MailingLog.objects.filter(status=MailingLog.Status.SENT).count()


@pytest.mark.django_db
def test_packages_zero_state_hides_trust_badge(client, user, package):
    MailingLog.objects.filter(status=MailingLog.Status.SENT).delete()

    client.force_login(user)
    response = client.get(reverse("payment_packages"))

    assert response.status_code == 200
    assert response.context["successful_sends_count"] == 0
    assert "envíos exitosos en la plataforma" not in response.content.decode()


@pytest.mark.django_db
def test_packages_page_is_public(client, package):
    """Anonymous visitors can view the pricing page without being redirected."""
    response = client.get(reverse("payment_packages"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_packages_anonymous_cta_redirects_to_login(client, package):
    """Anonymous visitors see a login-redirect link instead of a checkout form."""
    response = client.get(reverse("payment_packages"))
    html = response.content.decode()
    assert "/accounts/login/?next=/payments/paquetes/" in html
    checkout_url = reverse("create_checkout", args=[package.pk])
    assert f'action="{checkout_url}"' not in html


@pytest.mark.django_db
def test_packages_authenticated_cta_shows_checkout_form(client, user, package):
    """Authenticated users still see the POST form pointing to create_checkout."""
    client.force_login(user)
    response = client.get(reverse("payment_packages"))
    html = response.content.decode()
    checkout_url = reverse("create_checkout", args=[package.pk])
    assert f'action="{checkout_url}"' in html
    assert "/accounts/login/?next=/payments/paquetes/" not in html
