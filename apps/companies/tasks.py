import logging
import traceback
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from .models import CompanyImportBatch
from .importers import import_companies_from_xlsx

logger = logging.getLogger(__name__)


@shared_task
def process_company_import(batch_id):
    try:
        batch = CompanyImportBatch.objects.get(id=batch_id)
    except CompanyImportBatch.DoesNotExist:
        return

    batch.status = "PROCESSING"
    batch.save(update_fields=["status", "updated_at"])

    try:
        created, updated, errors, blacklisted_skipped = import_companies_from_xlsx(batch.file.path)

        try:
            batch.file.delete(save=False)
        except FileNotFoundError:
            pass
        batch.file.name = ""

        batch.created_count = created
        batch.updated_count = updated
        batch.blacklisted_skipped = blacklisted_skipped
        batch.error_log = errors
        batch.status = "COMPLETED"
        batch.save(update_fields=["file", "status", "created_count", "updated_count", "blacklisted_skipped", "error_log", "updated_at"])

    except Exception as e:
        batch.status = "FAILED"
        batch.error_log = [
            f"Error del sistema: {str(e)}",
            traceback.format_exc(),
            {"phase": "process", "file_path": batch.file.name},
        ]
        batch.save(update_fields=["status", "error_log", "updated_at"])


@shared_task
def purge_stale_company_import_files():
    cutoff = timezone.now() - timedelta(days=settings.COMPANY_IMPORT_FILE_RETENTION_DAYS)
    stale = CompanyImportBatch.objects.filter(created_at__lt=cutoff).exclude(file="")

    deleted = 0
    missing = 0
    errored = 0

    for batch in stale:
        try:
            if batch.file.storage.exists(batch.file.name):
                batch.file.delete(save=False)
                deleted += 1
            else:
                missing += 1
            batch.file.name = ""
            batch.save(update_fields=["file", "updated_at"])
        except Exception as exc:
            logger.error("purge_stale_company_import_files: error purging batch %s: %s", batch.id, exc)
            errored += 1

    logger.info(
        "purge_stale_company_import_files: deleted=%d missing=%d errored=%d",
        deleted,
        missing,
        errored,
    )
