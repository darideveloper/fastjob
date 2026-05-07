"""
Tests for the CompanyImportBatch admin progress endpoint and change-form widget.

The admin polls `progress_json` every 2 s during a live import to keep the
operator dashboard advancing without manual refresh, so the JSON shape and
auth gating are both load-bearing.
"""
import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from apps.companies.models import CompanyImportBatch


@pytest.fixture
def admin_client(db):
    User = get_user_model()
    User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="adminpass",
    )
    client = Client()
    client.login(username="admin@example.com", password="adminpass")
    return client


def _progress_url(batch_id):
    return reverse("admin:companies_companyimportbatch_progress", args=[batch_id])


@pytest.mark.django_db
def test_progress_endpoint_returns_expected_shape_for_processing_batch(admin_client):
    batch = CompanyImportBatch.objects.create(
        status="PROCESSING",
        total_rows=10,
        processed_rows=4,
        created_count=3,
        updated_count=1,
        blacklisted_skipped=2,
        error_log=["fila 5: email inválido", "fila 7: nombre vacío"],
    )

    response = admin_client.get(_progress_url(batch.id))

    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {
        "status",
        "total_rows",
        "processed_rows",
        "created_count",
        "updated_count",
        "blacklisted_skipped",
        "error_count",
    }
    assert data["status"] == "PROCESSING"
    assert isinstance(data["total_rows"], int)
    assert isinstance(data["processed_rows"], int)
    assert data["total_rows"] == 10
    assert data["processed_rows"] == 4
    assert data["created_count"] == 3
    assert data["updated_count"] == 1
    assert data["blacklisted_skipped"] == 2
    assert data["error_count"] == 2  # len(error_log)


@pytest.mark.django_db
def test_progress_endpoint_error_count_handles_empty_log(admin_client):
    batch = CompanyImportBatch.objects.create(status="PROCESSING")

    response = admin_client.get(_progress_url(batch.id))

    assert response.status_code == 200
    assert response.json()["error_count"] == 0


@pytest.mark.django_db
def test_progress_endpoint_redirects_anonymous_to_admin_login(db):
    batch = CompanyImportBatch.objects.create(status="PROCESSING")

    client = Client()
    response = client.get(_progress_url(batch.id))

    # admin_site.admin_view bounces unauthenticated requests to the admin
    # login page rather than returning 401.
    assert response.status_code == 302
    assert "/admin/login" in response["Location"]


@pytest.mark.django_db
def test_progress_endpoint_returns_404_for_missing_batch(admin_client):
    response = admin_client.get(_progress_url(999999))
    assert response.status_code == 404


@pytest.mark.django_db
def test_change_form_for_processing_batch_includes_progress_widget(admin_client):
    batch = CompanyImportBatch.objects.create(
        status="PROCESSING",
        total_rows=5,
        processed_rows=2,
    )
    url = reverse("admin:companies_companyimportbatch_change", args=[batch.id])

    response = admin_client.get(url)

    assert response.status_code == 200
    body = response.content.decode("utf-8")
    assert 'id="import-progress"' in body
    assert 'data-status="PROCESSING"' in body
    assert f'data-batch-id="{batch.id}"' in body


@pytest.mark.django_db
def test_change_form_for_completed_batch_marks_widget_as_completed(admin_client):
    batch = CompanyImportBatch.objects.create(
        status="COMPLETED",
        total_rows=5,
        processed_rows=5,
        created_count=5,
    )
    url = reverse("admin:companies_companyimportbatch_change", args=[batch.id])

    response = admin_client.get(url)

    assert response.status_code == 200
    body = response.content.decode("utf-8")
    # Widget is still emitted but tagged terminal so the JS leaves it hidden.
    assert 'id="import-progress"' in body
    assert 'data-status="COMPLETED"' in body
