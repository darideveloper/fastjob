from allauth.account.views import LoginView, LogoutView
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView, TemplateView

from config.health import healthz

# Custom 400 handler: Django's default `views.defaults.bad_request` swallows
# the originating exception (e.g. RequestDataTooBig, MultiPartParserError)
# and renders HTML, leaving XHR uploaders with an opaque "Bad Request" they
# can't decode. The replacement logs the real exception and returns JSON for
# AJAX clients — see config/error_handlers.py.
handler400 = "config.error_handlers.handler400"

# C3: this app is OAuth-only. Mounting `allauth.urls` would expose
# `/accounts/password/reset/`, `/accounts/email/`, `/accounts/password/change/`,
# etc. — paths that target accounts with no usable password and could be used
# to seize OAuth-only accounts. We only mount the OAuth-relevant subset below.
urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", LoginView.as_view(), name="account_login"),
    path("accounts/logout/", LogoutView.as_view(), name="account_logout"),
    # `LoginView.get_context_data` calls reverse("account_signup") to populate
    # `signup_url`. With C3 we do not mount a signup form, so the name must
    # still resolve — register it as a redirect to the OAuth login page.
    path(
        "accounts/signup/",
        RedirectView.as_view(pattern_name="account_login", permanent=False),
        name="account_signup",
    ),
    # `socialaccount.urls` was historically mounted at `/accounts/3rdparty/`
    # by allauth.urls; preserve that shape so `socialaccount_connections` keeps
    # the same path. Provider URL modules carry their own `google/` /
    # `microsoft/` prefix internally, so mount them at `accounts/` (not
    # `accounts/google/`) to reproduce the original `/accounts/google/login/`
    # shape configured in the OAuth provider consoles.
    path("accounts/3rdparty/", include("allauth.socialaccount.urls")),
    path("accounts/", include("allauth.socialaccount.providers.google.urls")),
    path("accounts/", include("allauth.socialaccount.providers.microsoft.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("payments/", include("apps.payments.urls")),
    path("", include("apps.companies.urls")),
    path("healthz", healthz, name="healthz"),
    path("", include("apps.mailing.urls")),
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
]
