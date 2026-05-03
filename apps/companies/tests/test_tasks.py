import os
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.companies.models import CompanyImportBatch, Company
from apps.companies.tasks import process_company_import
from apps.companies.tests.test_importers import make_xlsx


@pytest.mark.django_db
def test_process_company_import_task_success():
    # Make a dummy excel file using the helper from test_importers
    path = make_xlsx(
        ["empresa", "email", "actividad", "poblacion"],
        [
            ["Acme", "hr@acme.com", "Tech", "Madrid"],
        ],
    )
    
    with open(path, "rb") as f:
        file_content = f.read()

    # Create the batch manually simulating an upload
    uploaded_file = SimpleUploadedFile("test.xlsx", file_content, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    batch = CompanyImportBatch.objects.create(file=uploaded_file, status="PENDING")

    # Run the task synchronously (tests execute eagerly)
    process_company_import(batch.id)

    # Reload batch and assert status
    batch.refresh_from_db()
    assert batch.status == "COMPLETED"
    assert batch.created_count == 1
    assert batch.updated_count == 0
    assert batch.error_log == []

    assert Company.objects.count() == 1

    os.remove(path)


@pytest.mark.django_db
def test_process_company_import_task_handles_invalid_file():
    # Provide a text file instead of an excel file to force an error
    uploaded_file = SimpleUploadedFile("test.xlsx", b"not a real excel file", content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    batch = CompanyImportBatch.objects.create(file=uploaded_file, status="PENDING")

    process_company_import(batch.id)

    batch.refresh_from_db()
    assert batch.status == "FAILED"
    assert batch.created_count == 0
    assert batch.error_log
    assert "Error del sistema" in batch.error_log[0]
