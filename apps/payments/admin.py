from django.contrib import admin
from .models import CreditPackage, StripePayment


@admin.register(CreditPackage)
class CreditPackageAdmin(admin.ModelAdmin):
    list_display = ("name", "price_eur", "credits", "stripe_price_id", "is_active", "order")
    list_editable = ("is_active", "order")
    ordering = ("order", "price_eur")


@admin.register(StripePayment)
class StripePaymentAdmin(admin.ModelAdmin):
    list_display = ("user", "package", "amount_eur", "credits_granted", "status", "created_at", "completed_at")
    list_filter = ("status",)
    search_fields = ("user__email", "stripe_session_id")
    readonly_fields = ("user", "package", "stripe_session_id", "stripe_payment_intent", "amount_eur", "credits_granted", "status", "created_at", "completed_at")
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False
