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
                "fields": ("global_send_interval_minutes", "company_cooldown_hours"),
                "description": (
                    "global_send_interval_minutes: minutos mínimos entre envíos por usuario. "
                    "company_cooldown_hours: horas antes de que una empresa pueda recibir otro CV."
                ),
            },
        )
    ]

    def has_add_permission(self, request):
        return not SystemSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


PREVIEW_CONTEXT = {
    "company_name": "Empresa Ejemplo S.L.",
    "cv_url": "https://example.com/cv/00000000-0000-0000-0000-000000000000/",
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
    preview_link.short_description = "Preview"


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
