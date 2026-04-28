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


@pytest.mark.django_db
def test_admin_preview_isolates_xss_in_iframe(client, staff_user, email_template):
    """C2 regression: a malicious body_html must NOT execute as script in the
    admin-origin DOM. Body is rendered inside `<iframe sandbox srcdoc>` whose
    document carries a `default-src 'none'` CSP, so the raw `<script>` tag
    appears only as escaped text inside the srcdoc attribute."""
    email_template.body_html = (
        '<p>hi {company_name}</p>'
        '<script>alert("xss")</script>'
        '<a href="{cv_url}">cv</a>'
        '<a href="{unsubscribe_url}">u</a>'
    )
    email_template.save(update_fields=["body_html"])

    client.force_login(staff_user)
    resp = client.get(f"/admin/mailing/emailtemplate/{email_template.pk}/preview/")
    assert resp.status_code == 200
    body = resp.content.decode()

    # The body is wrapped in a sandboxed iframe — not rendered into the admin DOM.
    assert "<iframe sandbox" in body
    assert 'srcdoc="' in body

    # The script payload appears ONLY HTML-attribute-escaped inside srcdoc
    # (i.e. as `&lt;script&gt;`). The unescaped tag must NOT appear in the
    # admin-origin document, which would mean it'd execute on render.
    # Find the iframe's srcdoc value boundary, then check the surrounding
    # admin-origin HTML separately.
    assert '&lt;script&gt;alert(' in body  # escaped form is fine
    # Verify no raw <script> tag escaped the iframe context. We split on the
    # iframe close tag and look at the rest of the page.
    pre_iframe, _, after_iframe = body.partition("</iframe>")
    # Before iframe: the admin chrome — must contain no <script>alert
    assert "<script>alert(" not in pre_iframe.split("<iframe")[0]
    # After iframe: also no payload leakage
    assert "<script>alert(" not in after_iframe

    # CSP meta tag is present in the iframe srcdoc payload (escaped form).
    assert "Content-Security-Policy" in body
    assert "default-src &#x27;none&#x27;" in body or "default-src &#39;none&#39;" in body
