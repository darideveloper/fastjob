from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import CV, User


class CVInline(admin.TabularInline):
    model = CV
    extra = 0
    fields = ("name", "file", "created_at")
    readonly_fields = ("created_at",)
    fk_name = "user"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "first_name", "last_name", "credits_remaining", "is_campaign_active", "linked_provider", "date_joined")
    list_filter = ("is_campaign_active", "is_staff", "is_active")
    search_fields = ("email", "first_name", "last_name", "stripe_customer_id")
    ordering = ("-date_joined",)
    readonly_fields = ("date_joined", "last_login", "linked_provider")
    inlines = [CVInline]

    fieldsets = BaseUserAdmin.fieldsets + (
        ("FastJob", {
            "fields": ("credits_remaining", "is_campaign_active", "active_cv", "area_filter", "location_filter", "stripe_customer_id"),
        }),
    )

    def linked_provider(self, obj):
        return obj.linked_provider or "—"
    linked_provider.short_description = "Proveedor OAuth"


@admin.register(CV)
class CVAdmin(admin.ModelAdmin):
    list_display = ("user", "name", "file", "created_at")
    search_fields = ("user__email", "name")
    readonly_fields = ("created_at",)
