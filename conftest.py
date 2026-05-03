"""Shared pytest fixtures for all FastJob tests."""
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone


@pytest.fixture
def user(db):
    User = get_user_model()
    return User.objects.create_user(
        username="tester",
        email="tester@example.com",
        password="pw",
        credits_remaining=10,
        is_campaign_active=True,
    )


@pytest.fixture
def user_with_cv(user):
    from apps.accounts.models import CV
    cv = CV.objects.create(
        user=user,
        file=SimpleUploadedFile("cv.pdf", b"%PDF-1.4 fake pdf", content_type="application/pdf"),
        name="CV de prueba",
    )
    user.active_cv = cv
    user.save(update_fields=["active_cv"])
    return user


@pytest.fixture
def google_linked_user(user_with_cv):
    """User with a linked Google account and a fresh, non-expired OAuth token."""
    from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
    from django.contrib.sites.models import Site

    app = SocialApp.objects.create(
        provider="google",
        name="Google",
        client_id="fake-client-id",
        secret="fake-secret",
    )
    app.sites.add(Site.objects.get_current())

    account = SocialAccount.objects.create(
        user=user_with_cv,
        provider="google",
        uid="12345",
    )
    SocialToken.objects.create(
        app=app,
        account=account,
        token="fake-access-token",
        token_secret="fake-refresh-token",
        expires_at=timezone.now() + timedelta(hours=1),
    )
    return user_with_cv


@pytest.fixture
def microsoft_linked_user(user_with_cv):
    from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
    from django.contrib.sites.models import Site

    app = SocialApp.objects.create(
        provider="microsoft",
        name="Microsoft",
        client_id="fake-ms-id",
        secret="fake-ms-secret",
    )
    app.sites.add(Site.objects.get_current())

    account = SocialAccount.objects.create(
        user=user_with_cv,
        provider="microsoft",
        uid="ms-uid-1",
    )
    SocialToken.objects.create(
        app=app,
        account=account,
        token="ms-access-token",
        token_secret="ms-refresh-token",
        expires_at=timezone.now() + timedelta(hours=1),
    )
    return user_with_cv


@pytest.fixture
def company(db):
    from apps.companies.models import Company, Area, Location
    area, _ = Area.objects.get_or_create(name="Tecnología")
    location, _ = Location.objects.get_or_create(name="Madrid")
    return Company.objects.create(
        email="hr@acme.com",
        name="Acme Corp",
        area=area,
        location=location,
    )


@pytest.fixture
def email_template(db):
    from apps.mailing.models import EmailTemplate
    return EmailTemplate.objects.create(
        name="Test Template",
        subject="Candidatura para {company_name}",
        body_html='<p>Hola {company_name}</p><a href="{cv_url}">CV</a><a href="{unsubscribe_url}">Baja</a>',
        is_active=True,
    )
