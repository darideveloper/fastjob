from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

from config.health import healthz

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("payments/", include("apps.payments.urls")),
    path("healthz", healthz, name="healthz"),
    path("", include("apps.mailing.urls")),
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
]
