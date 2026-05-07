import logging

from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.core.exceptions import (
    RequestDataTooBig,
    SuspiciousFileOperation,
    SuspiciousMultipartForm,
    TooManyFieldsSent,
)
from django.http import Http404, JsonResponse
from django.http.multipartparser import MultiPartParserError
from django.urls import path
from django.shortcuts import redirect, render
from django.utils.html import format_html

from .models import Company, Blacklist, Area, Location, CompanyImportBatch
from .tasks import process_company_import

logger = logging.getLogger(__name__)


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
            # Multipart parse can fail before form validation runs (oversize
            # body, truncated upload from a proxy with a tighter body cap,
            # malformed multipart). Django would normally surface these as a
            # generic 400 HTML page, which the XHR client renders as the
            # opaque "Error al subir el archivo" fallback. Catch them here so
            # operators get the real exception name in JSON and the logs.
            try:
                form = XlsxImportForm(request.POST, request.FILES)
            except (
                RequestDataTooBig,
                TooManyFieldsSent,
                SuspiciousMultipartForm,
                MultiPartParserError,
            ) as exc:
                logger.warning(
                    "import_xlsx_view: multipart parse failed: %s: %s",
                    type(exc).__name__,
                    exc,
                )
                diagnostic = (
                    f"No se pudo procesar la subida ({type(exc).__name__}): {exc}. "
                    f"Verifica el tamaño del archivo (límite "
                    f"{settings.COMPANY_IMPORT_MAX_FILE_MB} MB) y la configuración "
                    f"del proxy."
                )
                if _is_xhr(request):
                    return JsonResponse({"error": diagnostic}, status=400)
                messages.error(request, diagnostic)
                return redirect("..")
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

            batch = None
            try:
                batch = CompanyImportBatch.objects.create(status="PENDING")
                uploaded = form.cleaned_data["xlsx_file"]
                batch.file.save(uploaded.name, uploaded, save=True)
            except (OSError, SuspiciousFileOperation) as exc:
                if batch is not None:
                    batch.status = "FAILED"
                    batch.error_log = [{"phase": "upload", "error": str(exc)}]
                    batch.save(update_fields=["status", "error_log", "updated_at"])
                if _is_xhr(request):
                    return JsonResponse(
                        {"error": f"Error al guardar el archivo: {exc}"},
                        status=500,
                    )
                if batch is not None:
                    messages.error(
                        request,
                        format_html(
                            'Error al guardar el archivo. Importación <a href="/admin/companies/companyimportbatch/{}/change/">{}</a> marcada como FALLIDA.',
                            batch.id,
                            batch.id,
                        ),
                    )
                else:
                    messages.error(request, f"Error al guardar el archivo: {exc}")
                return redirect("..")
            except Exception as exc:
                # Catch-all for the upload path so non-file-write failures
                # (e.g. django.db.utils.ProgrammingError from schema drift, or
                # OperationalError if the DB is unreachable) surface a
                # diagnostic message naming the exception class — instead of
                # the upload XHR's generic fallback "Error al subir el
                # archivo. Por favor inténtalo de nuevo."
                logger.exception("import_xlsx_view: unhandled error during batch creation")
                if batch is not None:
                    try:
                        batch.status = "FAILED"
                        batch.error_log = [
                            {
                                "phase": "upload",
                                "error_class": type(exc).__name__,
                                "error": str(exc),
                            }
                        ]
                        batch.save(update_fields=["status", "error_log", "updated_at"])
                    except Exception:
                        # If the same underlying issue (e.g. schema drift)
                        # also blocks the FAILED save, do not mask the
                        # original error from the operator.
                        logger.exception(
                            "import_xlsx_view: failed to mark batch %s as FAILED",
                            getattr(batch, "id", None),
                        )
                diagnostic = f"Error inesperado: {type(exc).__name__}: {exc}"
                if _is_xhr(request):
                    return JsonResponse({"error": diagnostic}, status=500)
                messages.error(request, diagnostic)
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
    list_display = (
        "id",
        "status",
        "processed_rows",
        "total_rows",
        "created_count",
        "updated_count",
        "blacklisted_skipped",
        "created_at",
    )
    list_filter = ("status", "created_at")
    readonly_fields = (
        "status",
        "total_rows",
        "processed_rows",
        "created_count",
        "updated_count",
        "blacklisted_skipped",
        "error_log",
        "created_at",
        "updated_at",
    )
    change_form_template = "admin/companies/companyimportbatch/change_form.html"

    def get_urls(self):
        custom = [
            path(
                "<int:object_id>/progress/",
                self.admin_site.admin_view(self.progress_json),
                name="companies_companyimportbatch_progress",
            ),
        ]
        return custom + super().get_urls()

    def progress_json(self, request, object_id):
        try:
            batch = CompanyImportBatch.objects.only(
                "status",
                "total_rows",
                "processed_rows",
                "created_count",
                "updated_count",
                "blacklisted_skipped",
                "error_log",
            ).get(id=object_id)
        except CompanyImportBatch.DoesNotExist:
            raise Http404("Importación no encontrada")

        return JsonResponse(
            {
                "status": batch.status,
                "total_rows": batch.total_rows,
                "processed_rows": batch.processed_rows,
                "created_count": batch.created_count,
                "updated_count": batch.updated_count,
                "blacklisted_skipped": batch.blacklisted_skipped,
                "error_count": len(batch.error_log or []),
            }
        )
