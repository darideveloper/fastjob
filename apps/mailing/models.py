import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class SystemSettings(models.Model):
    global_send_interval_minutes = models.IntegerField(
        default=5,
        help_text="Minutos entre envíos por usuario (Slow-Drip)",
    )
    company_cooldown_hours = models.IntegerField(
        default=12,
        help_text="Horas que deben pasar antes de que una empresa reciba otro CV",
    )

    class Meta:
        verbose_name = "Configuración del Sistema"
        verbose_name_plural = "Configuración del Sistema"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # Singleton cannot be deleted

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Configuración del Sistema"


class EmailTemplate(models.Model):
    name = models.CharField(max_length=100, help_text="Nombre interno para identificar la plantilla")
    subject = models.CharField(
        max_length=300,
        help_text="Asunto del email. Placeholders: {company_name}",
    )
    body_html = models.TextField(
        help_text=(
            "Cuerpo HTML del email. Placeholders: {company_name}, {cv_url}, {unsubscribe_url}"
        ),
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Plantilla de Email"
        verbose_name_plural = "Plantillas de Email"

    def __str__(self):
        return self.name

    def render(self, company_name, cv_url, unsubscribe_url):
        context = {
            "company_name": company_name,
            "cv_url": cv_url,
            "unsubscribe_url": unsubscribe_url,
        }
        return (
            self.subject.format(**context),
            self.body_html.format(**context),
        )


class MailingLog(models.Model):
    class Status(models.TextChoices):
        SENT = "sent", "Enviado"
        FAILED = "failed", "Fallido"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mailing_logs")
    company = models.ForeignKey("companies.Company", on_delete=models.SET_NULL, null=True, related_name="mailing_logs")
    email_template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True)
    cv = models.ForeignKey("accounts.CV", on_delete=models.SET_NULL, null=True, blank=True, related_name="mailing_logs")
    cv_download_token = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    unsubscribe_token = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    sent_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.SENT)
    error_message = models.TextField(blank=True)
    company_email_snapshot = models.EmailField(blank=True)

    class Meta:
        verbose_name = "Registro de Envío"
        verbose_name_plural = "Registros de Envíos"
        ordering = ["-sent_at"]

    def save(self, *args, **kwargs):
        if self.company and not self.company_email_snapshot:
            self.company_email_snapshot = self.company.email
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} → {self.company_email_snapshot} ({self.sent_at:%Y-%m-%d %H:%M})"
