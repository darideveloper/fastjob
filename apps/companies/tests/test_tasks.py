import os
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone

from apps.companies.models import Company, CompanyImportBatch
from apps.companies.tasks import process_company_import, purge_stale_company_import_files
from apps.companies.tests.test_importers import make_xlsx


def _make_batch_with_local_file(tmp_path, filename="test.xlsx", content=None):
    path = make_xlsx(
        ["empresa", "email", "actividad", "poblacion"],
        [["Acme", "hr@acme.com", "Tech", "Madrid"]],
    )
    with open(path, "rb") as f:
        content = content or f.read()
    os.remove(path)

    uploaded_file = SimpleUploadedFile(filename, content, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    batch = CompanyImportBatch.objects.create(status="PENDING")
    batch.file.save(filename, uploaded_file, save=True)
    return batch


@pytest.mark.django_db
def test_process_company_import_task_success(tmp_path):
    with override_settings(COMPANY_IMPORT_LOCAL_PATH=str(tmp_path)):
        batch = _make_batch_with_local_file(tmp_path)
        file_name = batch.file.name

        process_company_import(batch.id)

        batch.refresh_from_db()
        assert batch.status == "COMPLETED"
        assert batch.created_count == 1
        assert batch.updated_count == 0
        assert batch.error_log == []
        assert Company.objects.count() == 1
        # File should be deleted on success
        assert not batch.file.name


@pytest.mark.django_db
def test_process_company_import_task_handles_invalid_file(tmp_path):
    with override_settings(COMPANY_IMPORT_LOCAL_PATH=str(tmp_path)):
        upload = SimpleUploadedFile("test.xlsx", b"not a real excel file", content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        batch = CompanyImportBatch.objects.create(status="PENDING")
        batch.file.save("test.xlsx", upload, save=True)
        file_abs_path = batch.file.path

        process_company_import(batch.id)

        batch.refresh_from_db()
        assert batch.status == "FAILED"
        assert batch.created_count == 0
        assert batch.error_log
        assert "Error del sistema" in batch.error_log[0]
        # File should be kept on failure
        assert os.path.exists(file_abs_path)


@pytest.mark.django_db
def test_successful_processing_deletes_local_file(tmp_path):
    with override_settings(COMPANY_IMPORT_LOCAL_PATH=str(tmp_path)):
        batch = _make_batch_with_local_file(tmp_path)
        file_abs_path = batch.file.path

        process_company_import(batch.id)

        batch.refresh_from_db()
        assert batch.status == "COMPLETED"
        assert not os.path.exists(file_abs_path)


@pytest.mark.django_db
def test_failed_processing_leaves_file_on_disk(tmp_path):
    with override_settings(COMPANY_IMPORT_LOCAL_PATH=str(tmp_path)):
        upload = SimpleUploadedFile("test.xlsx", b"not a real excel file")
        batch = CompanyImportBatch.objects.create(status="PENDING")
        batch.file.save("test.xlsx", upload, save=True)
        file_abs_path = batch.file.path

        process_company_import(batch.id)

        batch.refresh_from_db()
        assert batch.status == "FAILED"
        assert os.path.exists(file_abs_path)


@pytest.mark.django_db
def test_purge_removes_only_stale_files(tmp_path):
    with override_settings(
        COMPANY_IMPORT_LOCAL_PATH=str(tmp_path),
        COMPANY_IMPORT_FILE_RETENTION_DAYS=7,
    ):
        upload_old = SimpleUploadedFile("old.xlsx", b"data")
        old_batch = CompanyImportBatch.objects.create(status="FAILED")
        old_batch.file.save("old.xlsx", upload_old, save=True)
        old_file_path = old_batch.file.path
        # Back-date to exceed retention window
        CompanyImportBatch.objects.filter(id=old_batch.id).update(
            created_at=timezone.now() - timedelta(days=8)
        )

        upload_recent = SimpleUploadedFile("recent.xlsx", b"data")
        recent_batch = CompanyImportBatch.objects.create(status="FAILED")
        recent_batch.file.save("recent.xlsx", upload_recent, save=True)
        recent_file_path = recent_batch.file.path

        purge_stale_company_import_files()

        assert not os.path.exists(old_file_path)
        old_batch.refresh_from_db()
        assert not old_batch.file.name

        assert os.path.exists(recent_file_path)
        recent_batch.refresh_from_db()
        assert recent_batch.file.name
