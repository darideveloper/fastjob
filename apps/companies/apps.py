from django.apps import AppConfig


class CompaniesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.companies"
    verbose_name = "Empresas"

    def ready(self):
        from django.db.models.signals import post_delete, post_save

        from .models import Company
        from .queries import bust_filter_caches

        def _bust(sender, **kwargs):
            bust_filter_caches()

        post_save.connect(_bust, sender=Company)
        post_delete.connect(_bust, sender=Company)
