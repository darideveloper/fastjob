import string
import uuid
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.db import models
from django.conf import settings
from django.utils import timezone


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
        help_text="Minutos entre envíos por usuario (Slow-Drip)",
    )
    company_cooldown_hours = models.IntegerField(
        default=12,
        help_text="Horas que deben pasar antes de que una empresa reciba otro CV",
    )
    max_emails_per_day_per_user = models.IntegerField(
        default=50,
        help_text="Límite máximo de correos por usuario en 24 horas",
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
        validators=[MaxLengthValidator(EMAIL_BODY_MAX_LENGTH)],
        help_text=(
            "Cuerpo HTML del email. Placeholders: {company_name}, {cv_url}, {unsubscribe_url}. "
            f"Máximo {EMAIL_BODY_MAX_LENGTH:,} caracteres."
        ),
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

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

    def render(self, company_name, cv_url, unsubscribe_url):
        # H11: render via the restricted formatter — strips attribute and
        # item access from placeholders so `{cv_url.__class__}` resolves
        # to the bare `cv_url` value, and SafeDict leaves unknown keys
        # like `{typo}` as literal text instead of raising.
        context = SafeDict(
            company_name=company_name,
            cv_url=cv_url,
            unsubscribe_url=unsubscribe_url,
        )
        return (
            _SAFE_FORMATTER.vformat(self.subject, (), context),
            _SAFE_FORMATTER.vformat(self.body_html, (), context),
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
    unsubscribed_at = models.DateTimeField(null=True, blank=True)

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
