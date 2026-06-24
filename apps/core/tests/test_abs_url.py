import uuid

import pytest
from django.conf import settings
from django.test import override_settings
from django.urls import NoReverseMatch, reverse

from apps.core.urls import abs_url


@pytest.mark.django_db
def test_abs_url_returns_fully_qualified_url():
    expected = f"{settings.SITE_SCHEME}://{settings.SITE_DOMAIN}{reverse('dashboard')}"
    assert abs_url("dashboard") == expected


@pytest.mark.django_db
def test_abs_url_raises_for_unknown_view():
    with pytest.raises(NoReverseMatch):
        abs_url("does_not_exist")


@pytest.mark.django_db
@override_settings(SITE_SCHEME="http", SITE_DOMAIN="example.test")
def test_abs_url_respects_site_settings_overrides():
    assert abs_url("home") == "http://example.test/"


@pytest.mark.django_db
def test_abs_url_passes_positional_args_through():
    token = uuid.uuid4()
    expected = f"{settings.SITE_SCHEME}://{settings.SITE_DOMAIN}/unsubscribe/{token}/"
    assert abs_url("unsubscribe", token) == expected
