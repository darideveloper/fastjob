from django.db import models
from django.utils import timezone
from config.storage_backends import PrivateMediaStorage


class LowercaseFieldsMixin:
    """
    Mixin to automatically lowercase specific fields before saving.
    Usage: Define 'lowercase_fields = ["field1", "field2"]' in your model.
    """

    lowercase_fields = []

    def save(self, *args, **kwargs):
        for field_name in self.lowercase_fields:
            value = getattr(self, field_name, None)
            if value and isinstance(value, str):
                setattr(self, field_name, value.lower())
        super().save(*args, **kwargs)


class Area(LowercaseFieldsMixin, models.Model):
    name = models.CharField(max_length=200, unique=True)

    lowercase_fields = ["name"]

    class Meta:
        verbose_name = "Sector"
        verbose_name_plural = "Sectores"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Location(LowercaseFieldsMixin, models.Model):
    name = models.CharField(max_length=200, unique=True)

    lowercase_fields = ["name"]

    class Meta:
        verbose_name = "Localidad"
        verbose_name_plural = "Localidades"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Company(LowercaseFieldsMixin, models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=300)
    area = models.ForeignKey(
        Area, on_delete=models.SET_NULL, null=True, blank=True, related_name="companies"
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="companies",
    )
    address = models.CharField(max_length=500, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    province = models.CharField(max_length=100, blank=True)
    community = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    fax = models.CharField(max_length=50, blank=True)
    website = models.CharField(max_length=500, blank=True)

    last_received_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    lowercase_fields = ["email", "name", "address", "province", "community", "website"]

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} <{self.email}>"


class Blacklist(LowercaseFieldsMixin, models.Model):
    email = models.EmailField(unique=True)
    added_at = models.DateTimeField(default=timezone.now)
    reason = models.CharField(max_length=100, default="unsubscribe")

    lowercase_fields = ["email"]

    class Meta:
        verbose_name = "Lista Negra"
        verbose_name_plural = "Lista Negra"
        ordering = ["-added_at"]

    def __str__(self):
        return self.email


class CompanyImportBatch(models.Model):
    STATUS_CHOICES = (
        ("PENDING", "Pendiente"),
        ("PROCESSING", "Procesando"),
        ("COMPLETED", "Completado"),
        ("FAILED", "Fallido"),
    )

    file = models.FileField(upload_to="imports/companies/", storage=PrivateMediaStorage())
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    created_count = models.PositiveIntegerField(default=0)
    updated_count = models.PositiveIntegerField(default=0)
    error_log = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Importación de Empresas"
        verbose_name_plural = "Importaciones de Empresas"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Importación {self.id} - {self.get_status_display()} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
