"""
Tests for the 3-step presigned-upload flow:
  1. POST /admin/companies/company/presign-import-upload/  → presign endpoint
  2. PUT to returned URL (S3 or local /local-import-upload/)
  3. POST /admin/companies/company/import-xlsx/            → trigger endpoint
"""
import json
import uuid
from unittest.mock import ANY as unittest_ANY, MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.test import Client, override_settings

from apps.companies.models import CompanyImportBatch


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


PRESIGN_URL = "/admin/companies/company/presign-import-upload/"
TRIGGER_URL = "/admin/companies/company/import-xlsx/"

_LOCAL_DEV_SETTINGS = {
    "STORAGE_AWS": False,
    "COMPANY_IMPORT_MAX_FILE_MB": 100,
    "COMPANY_IMPORT_PRESIGN_EXPIRY_SECONDS": 600,
}

_S3_SETTINGS = {
    "STORAGE_AWS": True,
    "COMPANY_IMPORT_MAX_FILE_MB": 100,
    "COMPANY_IMPORT_PRESIGN_EXPIRY_SECONDS": 600,
    "AWS_STORAGE_BUCKET_NAME": "test-bucket",
    "AWS_S3_ENDPOINT_URL": "https://nyc3.digitaloceanspaces.com",
    "AWS_S3_REGION_NAME": "nyc3",
    "AWS_ACCESS_KEY_ID": "test-key",
    "AWS_SECRET_ACCESS_KEY": "test-secret",
    "IMPORTS_LOCATION": "fastjob/imports",
}


# ──────────────────────────────────────────────────────────────────────────────
# Presign endpoint — local dev (STORAGE_AWS=False)
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_presign_local_dev_happy_path(admin_client):
    with override_settings(**_LOCAL_DEV_SETTINGS):
        resp = admin_client.post(
            PRESIGN_URL,
            data=json.dumps({
                "filename": "companies.xlsx",
                "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "content_length": 1024,
            }),
            content_type="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

    assert resp.status_code == 200
    data = resp.json()
    # Local dev returns a URL to the local upload endpoint, NOT local_dev: True
    assert "local_dev" not in data
    assert data["url"] is not None
    assert "local-import-upload" in data["url"]
    assert "upload_uuid" in data
    assert data["key"].startswith("imports/")
    assert data["key"].endswith(".xlsx")
    # Content-Length must NOT be in headers (forbidden XHR header)
    assert "Content-Length" not in data.get("headers", {})
    assert "Content-Type" in data["headers"]

    batch = CompanyImportBatch.objects.get()
    assert batch.status == "PENDING"
    assert batch.original_filename == "companies.xlsx"
    assert str(batch.upload_uuid) == data["upload_uuid"]


@pytest.mark.django_db
def test_presign_local_dev_oversize_rejected(admin_client):
    with override_settings(**_LOCAL_DEV_SETTINGS):
        resp = admin_client.post(
            PRESIGN_URL,
            data=json.dumps({
                "filename": "big.xlsx",
                "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "content_length": 101 * 1024 * 1024,
            }),
            content_type="application/json",
        )

    assert resp.status_code == 400
    assert "excede" in resp.json()["error"]
    assert CompanyImportBatch.objects.count() == 0


@pytest.mark.django_db
def test_presign_local_dev_wrong_extension_rejected(admin_client):
    with override_settings(**_LOCAL_DEV_SETTINGS):
        resp = admin_client.post(
            PRESIGN_URL,
            data=json.dumps({
                "filename": "data.csv",
                "content_type": "text/csv",
                "content_length": 1024,
            }),
            content_type="application/json",
        )

    assert resp.status_code == 400
    assert ".xlsx" in resp.json()["error"]
    assert CompanyImportBatch.objects.count() == 0


def test_presign_non_admin_redirected_to_login(db):
    anon = Client()
    resp = anon.post(
        PRESIGN_URL,
        data=json.dumps({"filename": "x.xlsx", "content_type": "application/octet-stream", "content_length": 1}),
        content_type="application/json",
    )
    assert resp.status_code in (302, 403)


# ──────────────────────────────────────────────────────────────────────────────
# Local upload view (STORAGE_AWS=False only)
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_local_upload_view_saves_file(admin_client):
    """Local upload view saves the raw PUT body at the correct storage-relative path."""
    batch_uuid = uuid.uuid4()
    CompanyImportBatch.objects.create(
        status="PENDING",
        upload_uuid=batch_uuid,
        original_filename="companies.xlsx",
    )
    filename = "companies.xlsx"
    local_upload_url = f"/admin/companies/company/local-import-upload/{batch_uuid}/{filename}/"

    # FileField.storage is baked-in at class definition time; we verify the
    # save() call rather than fighting the cached storage instance.
    with override_settings(**_LOCAL_DEV_SETTINGS):
        with patch("apps.companies.admin.CompanyImportBatch.objects.get") as mock_get:
            batch_mock = MagicMock(spec=CompanyImportBatch)
            batch_mock.upload_uuid = batch_uuid
            batch_mock.file.name = ""
            storage_mock = MagicMock()
            batch_mock.file.storage = storage_mock
            mock_get.return_value = batch_mock

            resp = admin_client.put(
                local_upload_url,
                data=b"fake-xlsx-content",
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    storage_mock.save.assert_called_once_with(
        f"{batch_uuid}/{filename}", unittest_ANY
    )


@pytest.mark.django_db
def test_local_upload_view_replay_protection(admin_client):
    """A second PUT to the same key returns 409 if batch already has a file."""
    batch_uuid = uuid.uuid4()
    batch = CompanyImportBatch.objects.create(
        status="PENDING",
        upload_uuid=batch_uuid,
        original_filename="companies.xlsx",
    )
    batch.file.name = f"{batch_uuid}/companies.xlsx"  # already triggered
    batch.save(update_fields=["file"])

    url = f"/admin/companies/company/local-import-upload/{batch_uuid}/companies.xlsx/"

    with override_settings(**_LOCAL_DEV_SETTINGS):
        resp = admin_client.put(url, data=b"data", content_type="application/octet-stream")

    assert resp.status_code == 409


@pytest.mark.django_db
def test_local_upload_view_blocked_in_s3_mode(admin_client):
    batch_uuid = uuid.uuid4()
    url = f"/admin/companies/company/local-import-upload/{batch_uuid}/companies.xlsx/"

    with override_settings(**_S3_SETTINGS):
        resp = admin_client.put(url, data=b"data", content_type="application/octet-stream")

    assert resp.status_code == 403


# ──────────────────────────────────────────────────────────────────────────────
# Presign endpoint — S3 mode (STORAGE_AWS=True)
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_presign_s3_happy_path_returns_signed_url(admin_client):
    mock_s3 = MagicMock()
    mock_s3.generate_presigned_url.return_value = (
        "https://test-bucket.nyc3.digitaloceanspaces.com/fastjob/imports/test-uuid/companies.xlsx?sig=abc"
    )

    with override_settings(**_S3_SETTINGS):
        with patch("apps.companies.admin._s3_client", return_value=mock_s3):
            resp = admin_client.post(
                PRESIGN_URL,
                data=json.dumps({
                    "filename": "companies.xlsx",
                    "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "content_length": 5 * 1024 * 1024,
                }),
                content_type="application/json",
            )

    assert resp.status_code == 200
    data = resp.json()
    assert data["url"].startswith("https://")
    assert "upload_uuid" in data
    assert "batch_id" in data
    assert "Content-Length" not in data.get("headers", {})
    mock_s3.generate_presigned_url.assert_called_once()


@pytest.mark.django_db
def test_presign_s3_failure_marks_batch_failed(admin_client):
    from botocore.exceptions import ClientError

    mock_s3 = MagicMock()
    mock_s3.generate_presigned_url.side_effect = ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}}, "GeneratePresignedUrl"
    )

    with override_settings(**_S3_SETTINGS):
        with patch("apps.companies.admin._s3_client", return_value=mock_s3):
            resp = admin_client.post(
                PRESIGN_URL,
                data=json.dumps({
                    "filename": "companies.xlsx",
                    "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "content_length": 1024,
                }),
                content_type="application/json",
            )

    assert resp.status_code == 500
    batch = CompanyImportBatch.objects.get()
    assert batch.status == "FAILED"
    assert batch.error_log[0]["phase"] == "presign"


# ──────────────────────────────────────────────────────────────────────────────
# Trigger endpoint (import_xlsx_view) — local dev
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_trigger_local_dev_happy_path(admin_client):
    batch_uuid = uuid.uuid4()
    batch = CompanyImportBatch.objects.create(
        status="PENDING",
        upload_uuid=batch_uuid,
        original_filename="companies.xlsx",
    )
    client_key = f"imports/{batch_uuid}/companies.xlsx"
    # storage_key = trigger strips "imports/" → "<uuid>/companies.xlsx"
    expected_storage_key = f"{batch_uuid}/companies.xlsx"

    with override_settings(**_LOCAL_DEV_SETTINGS):
        with patch("apps.companies.admin.process_company_import.delay") as mock_delay:
            resp = admin_client.post(
                TRIGGER_URL,
                data=json.dumps({"upload_uuid": str(batch_uuid), "key": client_key}),
                content_type="application/json",
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            )

    assert resp.status_code == 200
    data = resp.json()
    assert "redirect_url" in data
    mock_delay.assert_called_once_with(batch.id)

    batch.refresh_from_db()
    # Must be the storage-relative key, NOT the client_key (no "imports/" prefix)
    assert batch.file.name == expected_storage_key


@pytest.mark.django_db
def test_trigger_invalid_key_shape_rejected(admin_client):
    batch_uuid = uuid.uuid4()
    CompanyImportBatch.objects.create(
        status="PENDING", upload_uuid=batch_uuid, original_filename="f.xlsx"
    )

    with override_settings(**_LOCAL_DEV_SETTINGS):
        resp = admin_client.post(
            TRIGGER_URL,
            data=json.dumps({"upload_uuid": str(batch_uuid), "key": "../../etc/passwd"}),
            content_type="application/json",
        )

    assert resp.status_code == 400


@pytest.mark.django_db
def test_trigger_replay_protection_returns_409(admin_client):
    """A second trigger POST after the batch already has a file must return 409."""
    batch_uuid = uuid.uuid4()
    client_key = f"imports/{batch_uuid}/companies.xlsx"
    batch = CompanyImportBatch.objects.create(
        status="PROCESSING",
        upload_uuid=batch_uuid,
        original_filename="companies.xlsx",
    )
    batch.file.name = f"{batch_uuid}/companies.xlsx"
    batch.save(update_fields=["file"])

    with override_settings(**_LOCAL_DEV_SETTINGS):
        with patch("apps.companies.admin.process_company_import.delay") as mock_delay:
            resp = admin_client.post(
                TRIGGER_URL,
                data=json.dumps({"upload_uuid": str(batch_uuid), "key": client_key}),
                content_type="application/json",
            )

    assert resp.status_code == 409
    mock_delay.assert_not_called()


@pytest.mark.django_db
def test_trigger_unknown_uuid_returns_400(admin_client):
    phantom_uuid = uuid.uuid4()
    key = f"imports/{phantom_uuid}/companies.xlsx"

    with override_settings(**_LOCAL_DEV_SETTINGS):
        resp = admin_client.post(
            TRIGGER_URL,
            data=json.dumps({"upload_uuid": str(phantom_uuid), "key": key}),
            content_type="application/json",
        )

    assert resp.status_code == 400


# ──────────────────────────────────────────────────────────────────────────────
# Full local dev end-to-end: local upload → trigger → task dispatched
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_local_dev_end_to_end_upload_then_trigger(admin_client):
    """Verifies the full local-dev 3-step flow: local upload → trigger → task dispatched,
    and that batch.file.name is set to the storage-relative key (no 'imports/' prefix)."""
    batch_uuid = uuid.uuid4()
    sanitized = "companies.xlsx"
    CompanyImportBatch.objects.create(
        status="PENDING",
        upload_uuid=batch_uuid,
        original_filename="companies.xlsx",
    )
    local_upload_url = f"/admin/companies/company/local-import-upload/{batch_uuid}/{sanitized}/"
    client_key = f"imports/{batch_uuid}/{sanitized}"

    with override_settings(**_LOCAL_DEV_SETTINGS):
        # Step 2: PUT file to local endpoint (mock storage so we don't hit disk)
        with patch("apps.companies.admin.CompanyImportBatch.objects.get") as mock_get_upload:
            batch_mock = MagicMock(spec=CompanyImportBatch)
            batch_mock.upload_uuid = batch_uuid
            batch_mock.file.name = ""
            batch_mock.file.storage = MagicMock()
            mock_get_upload.return_value = batch_mock

            put_resp = admin_client.put(
                local_upload_url,
                data=b"fake-xlsx",
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        assert put_resp.status_code == 200

        # Step 3: trigger (use the real batch from DB)
        with patch("apps.companies.admin.process_company_import.delay") as mock_delay:
            trigger_resp = admin_client.post(
                TRIGGER_URL,
                data=json.dumps({"upload_uuid": str(batch_uuid), "key": client_key}),
                content_type="application/json",
            )

    assert trigger_resp.status_code == 200
    mock_delay.assert_called_once()

    batch = CompanyImportBatch.objects.get(upload_uuid=batch_uuid)
    # Must be the storage-relative key — trigger must strip "imports/" prefix
    assert batch.file.name == f"{batch_uuid}/{sanitized}"


# ──────────────────────────────────────────────────────────────────────────────
# Trigger endpoint — S3 mode
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_trigger_s3_key_not_found_returns_400(admin_client):
    batch_uuid = uuid.uuid4()
    key = f"imports/{batch_uuid}/companies.xlsx"
    CompanyImportBatch.objects.create(
        status="PENDING", upload_uuid=batch_uuid, original_filename="companies.xlsx"
    )

    mock_storage = MagicMock()
    mock_storage.exists.return_value = False

    with override_settings(**_S3_SETTINGS):
        with patch("apps.companies.admin.process_company_import.delay"):
            with patch(
                "apps.companies.admin.CompanyImportBatch.objects.get"
            ) as mock_get:
                batch_mock = MagicMock(spec=CompanyImportBatch)
                batch_mock.upload_uuid = batch_uuid
                batch_mock.file.name = ""
                batch_mock.file.storage = mock_storage
                batch_mock.id = 998
                mock_get.return_value = batch_mock

                resp = admin_client.post(
                    TRIGGER_URL,
                    data=json.dumps({"upload_uuid": str(batch_uuid), "key": key}),
                    content_type="application/json",
                )

    assert resp.status_code == 400


@pytest.mark.django_db
def test_trigger_s3_happy_path(admin_client):
    batch_uuid = uuid.uuid4()
    key = f"imports/{batch_uuid}/companies.xlsx"
    CompanyImportBatch.objects.create(
        status="PENDING", upload_uuid=batch_uuid, original_filename="companies.xlsx"
    )

    with override_settings(**_S3_SETTINGS):
        with patch("apps.companies.admin.process_company_import.delay") as mock_delay:
            with patch(
                "apps.companies.admin.CompanyImportBatch.objects.get"
            ) as mock_get:
                batch_mock = MagicMock(spec=CompanyImportBatch)
                batch_mock.upload_uuid = batch_uuid
                batch_mock.file.name = ""
                storage_mock = MagicMock()
                storage_mock.exists.return_value = True
                storage_mock.size.return_value = 1024
                batch_mock.file.storage = storage_mock
                batch_mock.id = 999
                mock_get.return_value = batch_mock

                resp = admin_client.post(
                    TRIGGER_URL,
                    data=json.dumps({"upload_uuid": str(batch_uuid), "key": key}),
                    content_type="application/json",
                )

    assert resp.status_code == 200
    mock_delay.assert_called_once_with(batch_mock.id)


# ──────────────────────────────────────────────────────────────────────────────
# GET import page renders
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_import_page_get_renders(admin_client):
    with override_settings(**_LOCAL_DEV_SETTINGS):
        resp = admin_client.get(TRIGGER_URL)

    assert resp.status_code == 200
    assert b"xlsx" in resp.content or b"Importar" in resp.content


# ──────────────────────────────────────────────────────────────────────────────
# Filename sanitization
# ──────────────────────────────────────────────────────────────────────────────

def test_sanitize_filename_normalises_non_ascii():
    from apps.companies.admin import _sanitize_filename

    # Ñ+A (no space) → NA
    assert _sanitize_filename("BBDDESPAÑA-575.xlsx") == "BBDDESPANA-575.xlsx"
    # Ñ followed by space: space becomes underscore
    assert _sanitize_filename("BBDDESPAÑ A-575.xlsx") == "BBDDESPAN_A-575.xlsx"
    assert _sanitize_filename("Copy of España.xlsx") == "Copy_of_Espana.xlsx"
    assert _sanitize_filename("normal.xlsx") == "normal.xlsx"
