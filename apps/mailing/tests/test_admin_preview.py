"""Tests for the EmailTemplate admin preview view."""
import pytest
from django.contrib.auth import get_user_model


@pytest.fixture
def staff_user(db):
    return get_user_model().objects.create_superuser("admin", "admin@example.com", "pw")


@pytest.mark.django_db
def test_admin_preview_renders_with_placeholders(client, staff_user, email_template):
    client.force_login(staff_user)
    resp = client.get(f"/admin/mailing/emailtemplate/{email_template.pk}/preview/")
    assert resp.status_code == 200
    body = resp.content.decode()
    assert "Empresa Ejemplo S.L." in body
    assert "example.com/cv/" in body


@pytest.mark.django_db
def test_admin_preview_surfaces_template_errors(client, staff_user, email_template):
    email_template.subject = "Hola {unknown_placeholder}"
    email_template.save(update_fields=["subject"])
    client.force_login(staff_user)
    resp = client.get(f"/admin/mailing/emailtemplate/{email_template.pk}/preview/")
    assert resp.status_code == 200
    assert b"Error al renderizar" in resp.content


@pytest.mark.django_db
def test_admin_preview_requires_staff(client, user, email_template):
    client.force_login(user)
    resp = client.get(f"/admin/mailing/emailtemplate/{email_template.pk}/preview/")
    # Non-staff get redirected to admin login.
    assert resp.status_code in (302, 403)
