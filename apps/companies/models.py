import uuid

from django.core.files.storage import storages
from django.db import models
from django.utils import timezone


def _imports_storage():
    # Referenced by migration 0010_alter_companyimportbatch_file as
    # apps.companies.models._imports_storage — renaming or moving requires a
    # follow-up migration so historical playback still resolves the import.
    return storages["imports"]


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
    name = models.CharField(max_length=200, unique=True, verbose_name="Nombre")

    lowercase_fields = ["name"]

    class Meta:
        verbose_name = "Sector"
        verbose_name_plural = "Sectores"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Location(LowercaseFieldsMixin, models.Model):
    name = models.CharField(max_length=200, unique=True, verbose_name="Nombre")

    lowercase_fields = ["name"]

    class Meta:
        verbose_name = "Localidad"
        verbose_name_plural = "Localidades"
        ordering = ["name"]

    def __str__(self):
        return self.name


class SubArea(LowercaseFieldsMixin, models.Model):
    name = models.CharField(max_length=200, unique=True, verbose_name="Nombre")

    lowercase_fields = ["name"]

    class Meta:
        verbose_name = "Subactividad"
        verbose_name_plural = "Subactividades"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Company(LowercaseFieldsMixin, models.Model):
    email = models.EmailField(unique=True, verbose_name="Email")
    name = models.CharField(max_length=300, verbose_name="Nombre")
    area = models.ForeignKey(
        Area, on_delete=models.SET_NULL, null=True, blank=True, related_name="companies", verbose_name="Sector"
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="companies",
        verbose_name="Localidad",
    )
    sub_area = models.ForeignKey(
        SubArea,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="companies",
        verbose_name="Subactividad",
    )
    address = models.CharField(max_length=500, blank=True, verbose_name="Dirección")
    zip_code = models.CharField(max_length=20, blank=True, verbose_name="Código postal")
    province = models.CharField(max_length=100, blank=True, verbose_name="Provincia")
    community = models.CharField(max_length=100, blank=True, verbose_name="Comunidad")
    phone = models.CharField(max_length=50, blank=True, verbose_name="Teléfono")
    fax = models.CharField(max_length=50, blank=True, verbose_name="Fax")
    website = models.CharField(max_length=500, blank=True, verbose_name="Sitio web")

    last_received_at = models.DateTimeField(null=True, blank=True, verbose_name="Último envío recibido")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creada el")

    lowercase_fields = ["email", "name", "address", "province", "community", "website"]

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} <{self.email}>"


class Blacklist(LowercaseFieldsMixin, models.Model):
    email = models.EmailField(unique=True, verbose_name="Email")
    added_at = models.DateTimeField(default=timezone.now, verbose_name="Añadido el")
    reason = models.CharField(max_length=100, default="unsubscribe", verbose_name="Motivo")

    lowercase_fields = ["email"]

    class Meta:
        verbose_name = "Lista Negra"
        verbose_name_plural = "Lista Negra"
        ordering = ["-added_at"]

    def __str__(self):
        return self.email

    @classmethod
    def add(cls, email, reason="unsubscribe"):
        normalized = (email or "").strip().lower()
        if not normalized:
            raise ValueError("empty email")
        return cls.objects.get_or_create(
            email=normalized,
            defaults={"reason": reason, "added_at": timezone.now()},
        )


class CompanyImportBatch(models.Model):
    STATUS_CHOICES = (
        ("PENDING", "Pendiente"),
        ("PROCESSING", "Procesando"),
        ("COMPLETED", "Completado"),
        ("FAILED", "Fallido"),
    )

    file = models.FileField(upload_to="companies/%Y/%m/%d/", storage=_imports_storage, blank=True, verbose_name="Archivo")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING", verbose_name="Estado")
    # UUID generated server-side at presign time; unique prevents replay attacks.
    upload_uuid = models.UUIDField(unique=True, null=True, blank=True, verbose_name="UUID de subida")
    original_filename = models.CharField(max_length=255, blank=True, verbose_name="Nombre de archivo original")
    total_rows = models.PositiveIntegerField(default=0, verbose_name="Total de filas")
    processed_rows = models.PositiveIntegerField(default=0, verbose_name="Filas procesadas")
    created_count = models.PositiveIntegerField(default=0, verbose_name="Empresas creadas")
    updated_count = models.PositiveIntegerField(default=0, verbose_name="Empresas actualizadas")
    blacklisted_skipped = models.IntegerField(default=0, verbose_name="Omitidas (lista negra)")
    error_log = models.JSONField(default=list, blank=True, verbose_name="Registro de errores")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creada el")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizada el")

    class Meta:
        verbose_name = "Importación de Empresas"
        verbose_name_plural = "Importaciones de Empresas"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Importación {self.id} - {self.get_status_display()} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
