from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    # OAuth flows assume one canonical account per email. Without the unique
    # constraint, the same email can be registered twice (e.g. once via Google
    # and once via Microsoft) and login becomes ambiguous — `authenticate()`
    # picks an arbitrary row.
    email = models.EmailField(unique=True)
    credits_remaining = models.IntegerField(default=0)
    is_campaign_active = models.BooleanField(default=False)
    active_cv = models.ForeignKey(
        "accounts.CV", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    area_filter = models.CharField(max_length=200, blank=True)
    location_filter = models.CharField(max_length=200, blank=True)
    stripe_customer_id = models.CharField(max_length=200, blank=True, db_index=True)

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

    def can_send(self):
        return self.is_campaign_active and self.credits_remaining > 0 and self.has_cv


class CV(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cvs")
    file = models.FileField(upload_to="cvs/")
    name = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "CV"
        verbose_name_plural = "CVs"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name or (self.file.name.rsplit("/", 1)[-1] if self.file else f"CV #{self.pk}")
