import json
import logging
import re
import unicodedata
import uuid

import boto3
from botocore.exceptions import ClientError, BotoCoreError

from django.conf import settings
from django.contrib import admin
from django.core.files.base import ContentFile
from django.http import Http404, JsonResponse
from django.urls import path, reverse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .models import Company, Blacklist, Area, Location, CompanyImportBatch
from .tasks import process_company_import

logger = logging.getLogger(__name__)

_ALLOWED_CONTENT_TYPES = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/octet-stream",
}

# Matches the client-facing key shape: imports/<uuid>/<sanitized-filename>.xlsx
_KEY_RE = re.compile(r"^imports/[0-9a-f-]{36}/[A-Za-z0-9_.,-]{1,200}\.xlsx$")


def _sanitize_filename(name):
    """NFKD-normalise → drop non-ASCII → collapse whitespace/slashes → truncate."""
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode("ascii")
    name = re.sub(r"[\s/\\]+", "_", name).strip("_")
    name = re.sub(r"[^A-Za-z0-9_.,\-]", "", name)
    name = name[:64] or "import"
    if not name.lower().endswith(".xlsx"):
        name = name + ".xlsx"
    return name


def _s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL or None,
        region_name=settings.AWS_S3_REGION_NAME,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


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

        # Local-dev upload endpoint: mirrors the S3 PUT so the JS flow is
        # identical in both environments. CSRF is exempt because the view is
        # protected by admin authentication + batch UUID validation; the file
        # body is sent as raw bytes (not a form), so CSRF's form-data check
        # would always fail regardless.
        local_upload = self.admin_site.admin_view(self.local_import_upload_view)
        local_upload.csrf_exempt = True  # tell CsrfViewMiddleware to skip this view

        custom = [
            path(
                "import-xlsx/",
                self.admin_site.admin_view(self.import_xlsx_view),
                name="companies_company_import_xlsx",
            ),
            path(
                "presign-import-upload/",
                self.admin_site.admin_view(self.presign_import_upload_view),
                name="companies_company_presign_import_upload",
            ),
            path(
                "local-import-upload/<str:batch_uuid_str>/<str:filename>/",
                local_upload,
                name="companies_company_local_import_upload",
            ),
        ]
        return custom + urls

    # ------------------------------------------------------------------
    # Step 1: presign endpoint
    # ------------------------------------------------------------------

    def presign_import_upload_view(self, request):
        if request.method != "POST":
            return JsonResponse({"error": "Método no permitido."}, status=405)

        try:
            body = json.loads(request.body)
        except (ValueError, UnicodeDecodeError):
            return JsonResponse({"error": "Cuerpo JSON inválido."}, status=400)

        filename = body.get("filename", "")
        content_type = body.get("content_type", "")
        try:
            content_length = int(body.get("content_length", 0))
        except (TypeError, ValueError):
            return JsonResponse({"error": "content_length debe ser un entero."}, status=400)

        if not filename.lower().endswith(".xlsx"):
            return JsonResponse({"error": "Solo se permiten archivos .xlsx."}, status=400)

        if content_type not in _ALLOWED_CONTENT_TYPES:
            return JsonResponse({"error": "Tipo de archivo no permitido."}, status=400)

        max_bytes = settings.COMPANY_IMPORT_MAX_FILE_MB * 1024 * 1024
        if content_length <= 0 or content_length > max_bytes:
            return JsonResponse(
                {"error": f"El archivo excede el límite de {settings.COMPANY_IMPORT_MAX_FILE_MB} MB."},
                status=400,
            )

        sanitized = _sanitize_filename(filename)
        batch_uuid = uuid.uuid4()
        # Client-facing key: "imports/<uuid>/<sanitized>"
        # Strip "imports/" to get the storage-relative key: "<uuid>/<sanitized>"
        # ImportsStorage.location = "fastjob/imports", so the full S3 key is
        # "fastjob/imports/<uuid>/<sanitized>". Both endpoints use this mapping.
        client_key = f"imports/{batch_uuid}/{sanitized}"
        storage_key = f"{batch_uuid}/{sanitized}"

        batch = CompanyImportBatch.objects.create(
            status="PENDING",
            upload_uuid=batch_uuid,
            original_filename=filename,
        )

        if not getattr(settings, "STORAGE_AWS", False):
            # Local dev: return a URL to the local upload endpoint that accepts
            # a raw PUT, mirroring the S3 PUT interface so the JS flow is identical.
            upload_url = reverse(
                "admin:companies_company_local_import_upload",
                kwargs={"batch_uuid_str": str(batch_uuid), "filename": sanitized},
            )
            return JsonResponse({
                "url": upload_url,
                "key": client_key,
                "headers": {"Content-Type": content_type},
                "expires_in": settings.COMPANY_IMPORT_PRESIGN_EXPIRY_SECONDS,
                "batch_id": batch.id,
                "upload_uuid": str(batch_uuid),
            })

        try:
            s3 = _s3_client()
            url = s3.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": settings.AWS_STORAGE_BUCKET_NAME,
                    # Full S3 key = IMPORTS_LOCATION + "/" + storage_key
                    "Key": f"{settings.IMPORTS_LOCATION}/{storage_key}",
                    "ContentType": content_type,
                    "ContentLength": content_length,
                },
                ExpiresIn=settings.COMPANY_IMPORT_PRESIGN_EXPIRY_SECONDS,
                HttpMethod="PUT",
            )
        except (ClientError, BotoCoreError) as exc:
            logger.error("presign_import_upload_view: S3 presign failed: %s", exc)
            batch.status = "FAILED"
            batch.error_log = [{"phase": "presign", "error": str(exc)}]
            batch.save(update_fields=["status", "error_log", "updated_at"])
            return JsonResponse(
                {"error": "No se pudo generar la URL de subida. Inténtalo de nuevo."},
                status=500,
            )

        return JsonResponse({
            "url": url,
            "key": client_key,
            # Content-Type must be sent by the browser to match the signed header.
            # Content-Length is omitted: browsers set it automatically and cannot
            # set it via xhr.setRequestHeader (forbidden header), so S3 validates
            # the auto-sent value against the signed ContentLength parameter.
            "headers": {"Content-Type": content_type},
            "expires_in": settings.COMPANY_IMPORT_PRESIGN_EXPIRY_SECONDS,
            "batch_id": batch.id,
            "upload_uuid": str(batch_uuid),
        })

    # ------------------------------------------------------------------
    # Step 2 (local dev only): receive the raw file body, save to storage
    # ------------------------------------------------------------------

    def local_import_upload_view(self, request, batch_uuid_str, filename):
        """Local-dev mirror of the S3 PUT. Saves the raw request body to the
        imports FileSystemStorage so the trigger + Celery task flow is identical
        to production. Only reachable when STORAGE_AWS=False."""
        if getattr(settings, "STORAGE_AWS", False):
            return JsonResponse({"error": "Not available in production."}, status=403)

        if request.method != "PUT":
            return JsonResponse({"error": "Método no permitido."}, status=405)

        try:
            batch_uuid = uuid.UUID(batch_uuid_str)
        except ValueError:
            return JsonResponse({"error": "UUID inválido."}, status=400)

        try:
            batch = CompanyImportBatch.objects.get(upload_uuid=batch_uuid, status="PENDING")
        except CompanyImportBatch.DoesNotExist:
            return JsonResponse({"error": "Subida no encontrada o ya procesada."}, status=404)

        if batch.file.name:
            return JsonResponse({"error": "Esta subida ya fue procesada."}, status=409)

        storage = batch.file.storage
        storage_key = f"{batch_uuid}/{filename}"
        storage.save(storage_key, ContentFile(request.body))

        return JsonResponse({"ok": True})

    # ------------------------------------------------------------------
    # Step 3: trigger view — bind the uploaded key to the batch row
    # ------------------------------------------------------------------

    def import_xlsx_view(self, request):
        if request.method == "POST":
            try:
                body = json.loads(request.body)
            except (ValueError, UnicodeDecodeError):
                return JsonResponse({"error": "Cuerpo JSON inválido."}, status=400)

            upload_uuid_str = body.get("upload_uuid", "")
            client_key = body.get("key", "")

            if not _KEY_RE.match(client_key):
                return JsonResponse(
                    {"error": "La subida no se completó. Vuelve a intentarlo."},
                    status=400,
                )

            try:
                batch_uuid = uuid.UUID(upload_uuid_str)
            except (ValueError, AttributeError):
                return JsonResponse({"error": "upload_uuid inválido."}, status=400)

            if str(batch_uuid) not in client_key:
                return JsonResponse({"error": "La clave no corresponde al UUID de subida."}, status=400)

            try:
                batch = CompanyImportBatch.objects.get(upload_uuid=batch_uuid)
            except CompanyImportBatch.DoesNotExist:
                return JsonResponse(
                    {"error": "La subida no se completó. Vuelve a intentarlo."},
                    status=400,
                )

            if batch.file.name:
                return JsonResponse({"error": "Esta subida ya fue procesada."}, status=409)

            # Strip the leading "imports/" segment: storage backends use a key
            # relative to their location prefix (IMPORTS_LOCATION for S3,
            # COMPANY_IMPORT_LOCAL_PATH for local dev). Both the local upload
            # view and the S3 presign build objects at "<uuid>/<sanitized>",
            # so the stripped key is always correct regardless of backend.
            storage_key = re.sub(r"^imports/", "", client_key)

            if getattr(settings, "STORAGE_AWS", False):
                storage = batch.file.storage
                if not storage.exists(storage_key):
                    return JsonResponse(
                        {"error": "La subida no se completó. Vuelve a intentarlo."},
                        status=400,
                    )
                max_bytes = settings.COMPANY_IMPORT_MAX_FILE_MB * 1024 * 1024
                try:
                    size = storage.size(storage_key)
                except Exception:
                    size = 0
                if size > max_bytes:
                    batch.status = "FAILED"
                    batch.error_log = [{"phase": "trigger", "error": "oversize"}]
                    batch.save(update_fields=["status", "error_log", "updated_at"])
                    return JsonResponse(
                        {"error": f"El archivo subido excede el límite de {settings.COMPANY_IMPORT_MAX_FILE_MB} MB."},
                        status=400,
                    )

            batch.file.name = storage_key
            batch.save(update_fields=["file", "updated_at"])

            process_company_import.delay(batch.id)

            return JsonResponse({
                "redirect_url": f"/admin/companies/companyimportbatch/{batch.id}/change/"
            })

        context = {
            **self.admin_site.each_context(request),
            "title": "Importar empresas desde Excel",
            "max_file_mb": settings.COMPANY_IMPORT_MAX_FILE_MB,
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
        "upload_uuid",
        "original_filename",
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
