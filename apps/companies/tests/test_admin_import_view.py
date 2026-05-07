"""
Tests for CompanyAdmin.import_xlsx_view — the 3-step upload flow.
"""
import io
from unittest.mock import patch

import openpyxl
import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings
from django.urls import reverse

from apps.companies.models import CompanyImportBatch


def make_xlsx_bytes(headers=None, rows=None):
    headers = headers or ["empresa", "email"]
    rows = rows or [["Acme", "hr@acme.com"]]
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.fixture
def admin_client(db):
    User = get_user_model()
    user = User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="adminpass",
    )
    client = Client()
    client.login(username="admin@example.com", password="adminpass")
    return client


IMPORT_URL = "/admin/companies/company/import-xlsx/"


@pytest.mark.django_db
def test_happy_path_creates_pending_batch_and_redirects(admin_client, tmp_path):
    xlsx_bytes = make_xlsx_bytes()
    upload = SimpleUploadedFile("companies.xlsx", xlsx_bytes, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with override_settings(
        COMPANY_IMPORT_LOCAL_PATH=str(tmp_path),
        CELERY_TASK_ALWAYS_EAGER=True,
    ):
        with patch("apps.companies.admin.process_company_import.delay") as mock_delay:
            response = admin_client.post(
                IMPORT_URL,
                {"xlsx_file": upload},
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
                HTTP_ACCEPT="application/json",
            )

    assert response.status_code == 302
    batch = CompanyImportBatch.objects.get()
    assert batch.status == "PENDING"
    assert batch.file.name != ""
    mock_delay.assert_called_once_with(batch.id)


@pytest.mark.django_db
def test_oversize_file_rejected_no_batch_created(admin_client, tmp_path):
    big_content = b"x" * (26 * 1024 * 1024)
    upload = SimpleUploadedFile("big.xlsx", big_content, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with override_settings(
        COMPANY_IMPORT_LOCAL_PATH=str(tmp_path),
        COMPANY_IMPORT_MAX_FILE_MB=25,
    ):
        with patch("apps.companies.admin.process_company_import.delay") as mock_delay:
            response = admin_client.post(
                IMPORT_URL,
                {"xlsx_file": upload},
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
                HTTP_ACCEPT="application/json",
            )

    assert response.status_code == 400
    import json
    body = json.loads(response.content)
    assert "demasiado grande" in body["error"]
    assert CompanyImportBatch.objects.count() == 0
    mock_delay.assert_not_called()


@pytest.mark.django_db
def test_non_xlsx_extension_rejected_no_batch_created(admin_client, tmp_path):
    upload = SimpleUploadedFile("data.csv", b"empresa,email\nAcme,hr@acme.com", content_type="text/csv")

    with override_settings(COMPANY_IMPORT_LOCAL_PATH=str(tmp_path)):
        with patch("apps.companies.admin.process_company_import.delay") as mock_delay:
            response = admin_client.post(
                IMPORT_URL,
                {"xlsx_file": upload},
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
                HTTP_ACCEPT="application/json",
            )

    assert response.status_code == 400
    import json
    body = json.loads(response.content)
    assert ".xlsx" in body["error"]
    assert CompanyImportBatch.objects.count() == 0
    mock_delay.assert_not_called()


@pytest.mark.django_db
def test_storage_failure_creates_failed_batch_and_returns_json_error(admin_client, tmp_path):
    xlsx_bytes = make_xlsx_bytes()
    upload = SimpleUploadedFile("companies.xlsx", xlsx_bytes, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with override_settings(COMPANY_IMPORT_LOCAL_PATH=str(tmp_path)):
        with patch("django.core.files.storage.FileSystemStorage._save", side_effect=OSError("disk full")):
            with patch("apps.companies.admin.process_company_import.delay") as mock_delay:
                response = admin_client.post(
                    IMPORT_URL,
                    {"xlsx_file": upload},
                    HTTP_X_REQUESTED_WITH="XMLHttpRequest",
                    HTTP_ACCEPT="application/json",
                )

    assert response.status_code == 500
    import json
    data = json.loads(response.content)
    assert "error" in data

    batch = CompanyImportBatch.objects.get()
    assert batch.status == "FAILED"
    assert any(
        isinstance(e, dict) and e.get("phase") == "upload"
        for e in batch.error_log
    )
    mock_delay.assert_not_called()
