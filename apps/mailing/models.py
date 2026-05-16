import string
import uuid
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.db import models
from django.conf import settings
from django.utils import timezone

from apps.companies.models import LowercaseFieldsMixin


# H14: hard cap on stored email-template body size. 50 000 chars is well
# above any reasonable HTML email (typical: 5–15 kB) but small enough that
# a runaway / pasted-in payload doesn't blow up render() memory or the
# preview iframe srcdoc attribute.
EMAIL_BODY_MAX_LENGTH = 50_000


class SafeDict(dict):
    """Mapping that returns the placeholder verbatim for missing keys, so
    a typo in a template doesn't blow up `EmailTemplate.render` and mark
    every queued send FAILED. Used together with `_SAFE_FORMATTER` below."""

    def __missing__(self, key):
        return "{" + key + "}"


class _SafeFormatter(string.Formatter):
    """Restricted str.Formatter that disables attribute walks (`{x.attr}`)
    and item access (`{x[0]}`) in templates.

    Without this, a malicious template like `{cv_url.__class__.__mro__[1]}`
    can walk Python's object graph and exfiltrate things via the format
    spec. By stripping everything after the first `.` or `[` from
    `field_name`, the formatter only ever resolves bare top-level keys.
    """

    def get_field(self, field_name, args, kwargs):
        # `field_name` is e.g. `cv_url`, `cv_url.__class__`, `cv_url[0]`.
        # We keep only the head and discard the rest.
        head = field_name.split(".", 1)[0].split("[", 1)[0]
        return self.get_value(head, args, kwargs), head


_SAFE_FORMATTER = _SafeFormatter()


class SystemSettings(models.Model):
    global_send_interval_minutes = models.IntegerField(
        default=5,
        verbose_name="Intervalo de envío (minutos)",
        help_text="Minutos entre envíos por usuario (Slow-Drip)",
    )
    company_cooldown_hours = models.IntegerField(
        default=12,
        verbose_name="Enfriamiento por empresa (horas)",
        help_text="Horas que deben pasar antes de que una empresa reciba otro CV",
    )
    max_emails_per_day_per_user = models.IntegerField(
        default=50,
        verbose_name="Máximo de envíos por usuario al día",
        help_text="Límite máximo de correos por usuario en 24 horas",
    )
    initial_free_credits = models.IntegerField(
        default=5,
        verbose_name="Envíos gratuitos iniciales",
        help_text="Envíos gratuitos otorgados al registrarse",
    )
    hidden_credit_multiplier = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=1.00,
        verbose_name="Multiplicador oculto de envíos",
        help_text="Multiplicador oculto para envíos extra (ej: 1.10 = 10% extra)",
    )
    save_emails_to_sent_folder = models.BooleanField(
        default=False,
        verbose_name="Guardar en carpeta Enviados",
        help_text="Si está activado, los correos enviados se guardarán en la carpeta 'Enviados' del usuario.",
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
    name = models.CharField(max_length=100, verbose_name="Nombre", help_text="Nombre interno para identificar la plantilla")
    subject = models.CharField(
        max_length=300,
        verbose_name="Asunto",
        help_text="Asunto del email. Placeholders: {company_name}",
    )
    body_html = models.TextField(
        validators=[MaxLengthValidator(EMAIL_BODY_MAX_LENGTH)],
        verbose_name="Cuerpo HTML",
        help_text=(
            "Cuerpo HTML del email. Placeholders: {company_name}, {unsubscribe_url}. "
            f"Máximo {EMAIL_BODY_MAX_LENGTH:,} caracteres."
        ),
    )
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creada el")

    class Meta:
        verbose_name = "Plantilla de Email"
        verbose_name_plural = "Plantillas de Email"

    def __str__(self):
        return self.name

    def clean(self):
        """Belt-and-braces re-check: a code path that bypasses validators
        (e.g. someone calling `save()` directly without `full_clean()`)
        would still trip this, since admin form-save invokes clean() too."""
        super().clean()
        if self.body_html and len(self.body_html) > EMAIL_BODY_MAX_LENGTH:
            raise ValidationError({
                "body_html": (
                    f"El cuerpo no puede superar {EMAIL_BODY_MAX_LENGTH:,} caracteres "
                    f"(actual: {len(self.body_html):,})."
                )
            })

    def render(self, company_name, unsubscribe_url):
        # H11: render via the restricted formatter — strips attribute and
        # item access from placeholders so `{unsubscribe_url.__class__}` resolves
        # to the bare `unsubscribe_url` value, and SafeDict leaves unknown keys
        # like `{typo}` as literal text instead of raising.
        context = SafeDict(
            company_name=company_name.upper(),
            unsubscribe_url=unsubscribe_url,
        )
        return (
            _SAFE_FORMATTER.vformat(self.subject, (), context),
            _SAFE_FORMATTER.vformat(self.body_html, (), context),
        )


class MailingLog(LowercaseFieldsMixin, models.Model):
    class Status(models.TextChoices):
        SENT = "sent", "Enviado"
        FAILED = "failed", "Fallido"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mailing_logs", verbose_name="Usuario")
    company = models.ForeignKey("companies.Company", on_delete=models.SET_NULL, null=True, related_name="mailing_logs", verbose_name="Empresa")
    email_template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True, verbose_name="Plantilla de email")
    cv = models.ForeignKey("accounts.CV", on_delete=models.SET_NULL, null=True, blank=True, related_name="mailing_logs", verbose_name="CV")
    cv_download_token = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True, verbose_name="Token de descarga del CV")
    unsubscribe_token = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True, verbose_name="Token de baja")
    sent_at = models.DateTimeField(default=timezone.now, verbose_name="Enviado el")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.SENT, verbose_name="Estado")
    error_message = models.TextField(blank=True, verbose_name="Mensaje de error")
    company_email_snapshot = models.EmailField(blank=True, verbose_name="Email de la empresa")
    unsubscribed_at = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de baja")

    lowercase_fields = ["company_email_snapshot"]

    class Meta:
        verbose_name = "Registro de Envío"
        verbose_name_plural = "Registros de Envíos"
        ordering = ["-sent_at"]

    def clean(self):
        super().clean()
        # If neither company nor snapshot is provided, we won't have an email
        # to track for blacklist/unsubscribe purposes.
        if not self.company and not self.company_email_snapshot:
            raise ValidationError(
                "Debe proporcionarse una empresa o un snapshot del email."
            )

    def save(self, *args, **kwargs):
        if self.company and not self.company_email_snapshot:
            self.company_email_snapshot = self.company.email
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} → {self.company_email_snapshot} ({self.sent_at:%Y-%m-%d %H:%M})"
