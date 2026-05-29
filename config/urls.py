from allauth.account.views import LoginView, LogoutView
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

from apps.core.views import HomeView
from config.health import healthz

# Custom error handlers: Django's defaults are replaced to provide:
# - Structured logging of the originating exception.
# - Consistent JSON responses for XHR/AJAX clients.
# See config/error_handlers.py for implementation details.
handler400 = "config.error_handlers.handler400"
handler404 = "config.error_handlers.handler404"
handler500 = "config.error_handlers.handler500"

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
    # Mounting `allauth.socialaccount.urls` at `/accounts/3rdparty/` is removed
    # to completely disable social account unlinking/connections management.
    # To prevent NoReverseMatch failures if allauth reverses socialaccount_signup,
    # we mount a defensive redirect to the standard login screen.
    path(
        "accounts/3rdparty/signup/",
        RedirectView.as_view(pattern_name="account_login", permanent=False),
        name="socialaccount_signup",
    ),
    path("accounts/", include("allauth.socialaccount.providers.google.urls")),
    path("accounts/", include("allauth.socialaccount.providers.microsoft.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("payments/", include("apps.payments.urls")),
    path("", include("apps.companies.urls")),
    path("healthz", healthz, name="healthz"),
    path("", include("apps.mailing.urls")),
    path("", HomeView.as_view(), name="home"),
]
