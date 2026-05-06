import tempfile
import traceback
from celery import shared_task

from .models import CompanyImportBatch
from .importers import import_companies_from_xlsx


@shared_task
def process_company_import(batch_id):
    try:
        batch = CompanyImportBatch.objects.get(id=batch_id)
    except CompanyImportBatch.DoesNotExist:
        return

    batch.status = "PROCESSING"
    batch.save(update_fields=["status", "updated_at"])

    try:
        # Download the file to a local NamedTemporaryFile
        # This ensures openpyxl can read it efficiently even if using S3 storage
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=True) as tmp:
            with batch.file.open("rb") as f:
                tmp.write(f.read())
            tmp.flush()

            # Process the local file
            created, updated, errors, blacklisted_skipped = import_companies_from_xlsx(tmp.name)

        batch.created_count = created
        batch.updated_count = updated
        batch.blacklisted_skipped = blacklisted_skipped
        batch.error_log = errors
        batch.status = "COMPLETED"
    except Exception as e:
        batch.status = "FAILED"
        batch.error_log = [f"Error del sistema: {str(e)}", traceback.format_exc()]

    batch.save(update_fields=["status", "created_count", "updated_count", "blacklisted_skipped", "error_log", "updated_at"])
