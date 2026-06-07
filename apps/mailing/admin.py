from django.contrib import admin
from django.http import Http404
from django.shortcuts import render
from django.urls import path
from django.utils.html import format_html

from .models import EmailTemplate, MailingLog, SystemSettings

# Strict CSP applied inside the preview iframe. `default-src 'none'` blocks
# scripts/objects/frames; `style-src 'unsafe-inline'` keeps inline styles working
# (templates rely on them); images allow data: + https: so legitimate logos load.
PREVIEW_CSP = (
    "default-src 'none'; "
    "style-src 'unsafe-inline'; "
    "img-src data: https:; "
    "font-src https: data:"
)


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    fieldsets = [
        (
            "Motor de Envío (Slow-Drip)",
            {
                "fields": (
                    "global_send_interval_minutes",
                    "company_cooldown_hours",
                    "max_emails_per_day_per_user",
                ),
                "description": (
                    "Controla el ritmo de envío. "
                    "El intervalo define los minutos mínimos entre envíos por usuario. "
                    "El enfriamiento por empresa evita enviar dos CVs a la misma empresa en menos horas de las configuradas. "
                    "El máximo diario limita el total de correos que un usuario puede enviar en 24 horas."
                ),
            },
        ),
        (
            "Créditos y Bonos",
            {
                "fields": (
                    "initial_free_credits",
                    "hidden_credit_multiplier",
                ),
                "description": (
                    "Los envíos gratuitos iniciales se otorgan automáticamente al registrarse. "
                    "El multiplicador oculto amplía el saldo efectivo de los usuarios sin modificar su crédito visible "
                    "(por ejemplo, 1.10 equivale a un 10% extra de margen)."
                ),
            },
        ),
        (
            "Branding de Emails",
            {
                "fields": (
                    "email_logo_url",
                    "email_brand_color",
                    "email_footer_text",
                    "low_credits_threshold",
                ),
                "description": (
                    "Configuración visual de los correos automáticos. "
                    "El logo aparece en la cabecera. "
                    "El color de marca se usa en la línea decorativa. "
                    "El texto de pie de página se incluye en todas las plantillas. "
                    "El umbral de créditos bajos define cuándo enviar alertas automáticas."
                ),
            },
        ),
        (
            "Página de Paquetes",
            {
                "fields": ("displayed_sends_floor",),
                "description": (
                    "Controla el contador de envíos exitosos mostrado públicamente en la página de paquetes. "
                    "Si el número real de envíos es inferior a este valor, se mostrará este valor en su lugar. "
                    "Usar 0 para mostrar siempre el valor real."
                ),
            },
        ),
    ]

    def has_add_permission(self, request):
        return not SystemSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


PREVIEW_CONTEXT = {
    "company_name": "Empresa Ejemplo S.L.",
    "unsubscribe_url": "https://example.com/unsubscribe/00000000-0000-0000-0000-000000000000/",
}


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "subject_preview", "is_active", "preview_link", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "subject")
    list_editable = ("is_active",)

    def get_urls(self):
        urls = super().get_urls()
        return [
            path(
                "<int:object_id>/preview/",
                self.admin_site.admin_view(self.preview_view),
                name="mailing_emailtemplate_preview",
            ),
        ] + urls

    def preview_view(self, request, object_id):
        try:
            obj = EmailTemplate.objects.get(pk=object_id)
        except EmailTemplate.DoesNotExist:
            raise Http404

        try:
            subject, body_html = obj.render(**PREVIEW_CONTEXT)
            error = None
        except Exception as exc:
            subject = ""
            body_html = ""
            error = str(exc)

        # Wrap the rendered body in a self-contained HTML doc that carries a
        # strict CSP meta tag. The doc is then placed in an iframe `srcdoc` in
        # the template — Django's auto-escape attribute-encodes the value, and
        # `sandbox` (without allow-scripts) blocks JS as a second line of
        # defence in browsers that ignore the meta CSP. Together these prevent
        # one staff user's malicious template from running JS in another's
        # admin session.
        preview_doc = (
            "<!doctype html><html><head>"
            f'<meta http-equiv="Content-Security-Policy" content="{PREVIEW_CSP}">'
            '<meta charset="utf-8">'
            "</head><body>"
            f"{body_html}"
            "</body></html>"
        ) if body_html else ""

        context = {
            **self.admin_site.each_context(request),
            "title": f"Vista previa — {obj.name}",
            "template_obj": obj,
            "subject": subject,
            "preview_doc": preview_doc,
            "error": error,
            "sample_values": PREVIEW_CONTEXT,
        }
        return render(request, "admin/mailing/emailtemplate/preview.html", context)

    def subject_preview(self, obj):
        return obj.subject[:60] + ("…" if len(obj.subject) > 60 else "")
    subject_preview.short_description = "Asunto"

    def preview_link(self, obj):
        return format_html('<a href="{}/preview/" target="_blank">Ver preview</a>', obj.pk)
    preview_link.short_description = "Vista previa"


@admin.register(MailingLog)
class MailingLogAdmin(admin.ModelAdmin):
    list_display = ("user", "company_email_snapshot", "status", "sent_at", "template_name")
    list_filter = ("status", "sent_at")
    search_fields = ("user__email", "company_email_snapshot")
    ordering = ("-sent_at",)
    readonly_fields = (
        "user", "company", "email_template", "cv", "cv_download_token",
        "unsubscribe_token", "sent_at", "status", "error_message", "company_email_snapshot",
    )

    def has_add_permission(self, request):
        return False

    def template_name(self, obj):
        return obj.email_template.name if obj.email_template else "—"
    template_name.short_description = "Plantilla"
