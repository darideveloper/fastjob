"""Regression test for the C3 OAuth-only URL surface.

`allauth.account.views.LoginView.get_context_data()` calls
`reverse('account_signup')` to populate `signup_url`. The C3 hardening
mounts only the OAuth subset of allauth (no signup form), which made the
reverse fail and surfaced as a hard HTTP 500 on `GET /accounts/login/`.

The fix registers the URL **name** `account_signup` against a
`RedirectView` that bounces to `account_login`. This test guards against
regressions of either: the named URL must exist, the login page must
render, and the redirect target must round-trip back to login.
"""
import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_login_get_renders_200(client):
    response = client.get("/accounts/login/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_signup_url_redirects_to_login(client):
    signup_url = reverse("account_signup")
    response = client.get(signup_url)
    assert response.status_code == 302
    assert response["Location"] == "/accounts/login/"

    followed = client.get(signup_url, follow=True)
    assert followed.status_code == 200


def test_account_signup_name_is_reversible():
    assert reverse("account_signup") == "/accounts/signup/"
