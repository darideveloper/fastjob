from django.contrib.auth.models import AbstractUser
from django.core.files.storage import storages
from django.db import models


def _private_storage():
    return storages["private"]


class User(AbstractUser):
    # OAuth flows assume one canonical account per email. Without the unique
    # constraint, the same email can be registered twice (e.g. once via Google
    # and once via Microsoft) and login becomes ambiguous — `authenticate()`
    # picks an arbitrary row.
    email = models.EmailField(unique=True)
    credits_remaining = models.IntegerField(default=0, verbose_name="Envíos disponibles")
    is_campaign_active = models.BooleanField(default=False, verbose_name="Campaña activa")
    active_cv = models.ForeignKey(
        "accounts.CV", on_delete=models.SET_NULL, null=True, blank=True, related_name="+", verbose_name="CV activo"
    )
    area_filters = models.ManyToManyField(
        "companies.Area", blank=True, related_name="users_m2m", verbose_name="Filtros de sector"
    )
    location_filters = models.ManyToManyField(
        "companies.Location", blank=True, related_name="users_m2m", verbose_name="Filtros de localidad"
    )
    stripe_customer_id = models.CharField(max_length=200, blank=True, db_index=True, verbose_name="ID de cliente Stripe")
    total_purchased_credits = models.IntegerField(default=0, verbose_name="Total de envíos comprados")
    campaign_pause_reason = models.CharField(max_length=20, blank=True, verbose_name="Razón de pausa de campaña")
    last_low_credits_warning_at = models.DateTimeField(null=True, blank=True, verbose_name="Última alerta de créditos bajos")

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return self.email

    @property
    def has_cv(self):
        return self.active_cv is not None and bool(self.active_cv.file)

    @property
    def linked_provider(self):
        social = self.socialaccount_set.first()
        return social.provider if social else None

    @property
    def visible_credits(self):
        return max(0, self.credits_remaining)

    def can_send(self):
        from apps.mailing.models import SystemSettings
        import math

        cfg = SystemSettings.get()
        # Hidden floor: ceil(total_purchased_credits * (multiplier - 1))
        # eligibility: credits_remaining > -hidden_floor
        extra_limit = math.ceil(self.total_purchased_credits * (float(cfg.hidden_credit_multiplier) - 1.0))
        
        return self.is_campaign_active and self.credits_remaining > -extra_limit and self.has_cv


class CV(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cvs", verbose_name="Usuario")
    file = models.FileField(upload_to="cvs/", storage=_private_storage, verbose_name="Archivo")
    name = models.CharField(max_length=200, blank=True, verbose_name="Nombre")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")

    class Meta:
        verbose_name = "CV"
        verbose_name_plural = "CVs"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name or (self.file.name.rsplit("/", 1)[-1] if self.file else f"CV #{self.pk}")
