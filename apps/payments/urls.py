from django.urls import path
from . import views

urlpatterns = [
    path("paquetes/", views.packages, name="payment_packages"),
    path("checkout/<int:package_id>/", views.create_checkout, name="create_checkout"),
    path("success/", views.payment_success, name="payment_success"),
    path("portal/", views.billing_portal, name="billing_portal"),
    path("webhook/", views.stripe_webhook, name="stripe_webhook"),
]
