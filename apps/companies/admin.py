from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.core.exceptions import SuspiciousFileOperation
from django.http import JsonResponse
from django.urls import path
from django.shortcuts import redirect, render
from django.utils.html import format_html

from .models import Company, Blacklist, Area, Location, CompanyImportBatch
from .tasks import process_company_import


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


class XlsxImportForm(forms.Form):
    xlsx_file = forms.FileField(
        label="Archivo Excel (.xlsx)",
        help_text=(
            "Columnas requeridas: empresa, email. Opcionales: actividad, direccion, cp, poblacion, "
            "provincia, comunidad, telefono, fax, website. "
            f"Tamaño máximo: {settings.COMPANY_IMPORT_MAX_FILE_MB} MB."
        ),
    )

    def clean_xlsx_file(self):
        f = self.cleaned_data["xlsx_file"]
        if not f.name.lower().endswith(".xlsx"):
            raise forms.ValidationError("Solo se permiten archivos .xlsx.")
        max_bytes = settings.COMPANY_IMPORT_MAX_FILE_MB * 1024 * 1024
        if f.size > max_bytes:
            raise forms.ValidationError(
                f"El archivo es demasiado grande ({f.size // (1024 * 1024)} MB). "
                f"El límite es {settings.COMPANY_IMPORT_MAX_FILE_MB} MB."
            )
        return f


def _is_xhr(request):
    return (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or "application/json" in request.headers.get("Accept", "")
    )


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "area", "location", "province", "created_at")
    list_filter = ("area", "location", "province", "community")
    search_fields = ("name", "email", "area__name", "location__name", "address", "website")
    ordering = ("name",)
    fieldsets = (
        (None, {
            "fields": ("name", "email")
        }),
        ("Taxonomía", {
            "fields": ("area", "location")
        }),
        ("Ubicación", {
            "fields": ("address", "zip_code", "province", "community")
        }),
        ("Contacto", {
            "fields": ("phone", "fax", "website")
        }),
        ("Metadatos", {
            "fields": ("last_received_at", "created_at"),
            "classes": ("collapse",)
        }),
    )
    readonly_fields = ("created_at",)
    change_list_template = "admin/companies/company/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("import-xlsx/", self.admin_site.admin_view(self.import_xlsx_view), name="companies_company_import_xlsx"),
        ]
        return custom + urls

    def import_xlsx_view(self, request):
        if request.method == "POST":
            form = XlsxImportForm(request.POST, request.FILES)
            if not form.is_valid():
                if _is_xhr(request):
                    first_error = next(
                        iter(form.errors.get("xlsx_file", [])),
                        "Archivo no válido.",
                    )
                    return JsonResponse({"error": first_error}, status=400)
                context = {
                    **self.admin_site.each_context(request),
                    "form": form,
                    "title": "Importar empresas desde Excel",
                }
                return render(request, "admin/companies/import_xlsx.html", context)

            batch = CompanyImportBatch.objects.create(status="PENDING")
            try:
                uploaded = form.cleaned_data["xlsx_file"]
                batch.file.save(uploaded.name, uploaded, save=True)
            except (OSError, SuspiciousFileOperation) as exc:
                batch.status = "FAILED"
                batch.error_log = [{"phase": "upload", "error": str(exc)}]
                batch.save(update_fields=["status", "error_log", "updated_at"])
                if _is_xhr(request):
                    return JsonResponse(
                        {"error": f"Error al guardar el archivo: {exc}"},
                        status=500,
                    )
                messages.error(
                    request,
                    format_html(
                        'Error al guardar el archivo. Importación <a href="/admin/companies/companyimportbatch/{}/change/">{}</a> marcada como FALLIDA.',
                        batch.id,
                        batch.id,
                    ),
                )
                return redirect("..")

            process_company_import.delay(batch.id)
            messages.success(
                request,
                format_html(
                    'La importación ha comenzado en segundo plano. '
                    'Puedes revisar el estado en <a href="/admin/companies/companyimportbatch/{}/change/">Importación {}</a>.',
                    batch.id,
                    batch.id,
                ),
            )
            return redirect("..")

        form = XlsxImportForm()
        context = {
            **self.admin_site.each_context(request),
            "form": form,
            "title": "Importar empresas desde Excel",
        }
        return render(request, "admin/companies/import_xlsx.html", context)


@admin.register(Blacklist)
class BlacklistAdmin(admin.ModelAdmin):
    list_display = ("email", "reason", "added_at")
    search_fields = ("email",)
    list_filter = ("reason",)
    ordering = ("-added_at",)

@admin.register(CompanyImportBatch)
class CompanyImportBatchAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "created_count", "updated_count", "blacklisted_skipped", "created_at")
    list_filter = ("status", "created_at")
    readonly_fields = ("status", "created_count", "updated_count", "blacklisted_skipped", "error_log", "created_at", "updated_at")
