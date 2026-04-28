"""C3 regression tests: this app is OAuth-only, so password / secondary-email
URLs from `allauth.urls` must NOT be mounted. Mounting them would expose
account-takeover paths against accounts that have no usable password (created
via `socialaccount.adapter.save_user`).

We assert URL surface area at the resolver level rather than via the test
client to side-step ALLOWED_HOSTS / middleware noise — `resolve()` is the
authoritative answer for "is this path mapped to a view".
"""
import pytest
from django.urls import NoReverseMatch, resolve, reverse
from django.urls.exceptions import Resolver404


FORBIDDEN_PATHS = [
    "/accounts/password/reset/",
    "/accounts/password/change/",
    "/accounts/password/set/",
    "/accounts/email/",
    "/accounts/confirm-email/",
    "/accounts/inactive/",
]


@pytest.mark.parametrize("path", FORBIDDEN_PATHS)
def test_password_and_email_routes_are_not_mounted(path):
    with pytest.raises(Resolver404):
        resolve(path)


def test_oauth_login_routes_still_resolve():
    # account_login + account_logout are explicit; OAuth provider entry points
    # must keep their original `/accounts/google/login/` shape so the redirect
    # URI registered in the OAuth provider console keeps working.
    assert reverse("account_login") == "/accounts/login/"
    assert reverse("account_logout") == "/accounts/logout/"
    assert reverse("google_login") == "/accounts/google/login/"
    assert reverse("microsoft_login") == "/accounts/microsoft/login/"


def test_socialaccount_connections_route_preserved():
    # socialaccount.urls used to be mounted at /accounts/3rdparty/ via
    # allauth.urls. Preserve that shape so any hardcoded references / docs /
    # bookmarks keep working.
    assert reverse("socialaccount_connections") == "/accounts/3rdparty/"


@pytest.mark.parametrize(
    "name",
    [
        "account_password_reset",
        "account_password_change",
        "account_email",
        "account_set_password",
    ],
)
def test_password_email_url_names_unreversible(name):
    with pytest.raises(NoReverseMatch):
        reverse(name)
