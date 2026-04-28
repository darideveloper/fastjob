"""C5 (security-fixes.md) regression: User.email is UNIQUE at the DB level.

Without this constraint, OAuth flows can produce two rows with the same
email (one from Google, one from Microsoft, or one created via the admin
plus one via OAuth). `authenticate()` then picks an arbitrary row, and
account ownership becomes ambiguous.
"""
import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction


@pytest.mark.django_db
def test_creating_two_users_with_same_email_raises_integrity_error():
    User = get_user_model()
    User.objects.create_user(username="a", email="dupe@example.com", password="pw")

    # Wrap in atomic so the failing INSERT doesn't poison the outer
    # transaction that pytest-django runs the test inside.
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            User.objects.create_user(username="b", email="dupe@example.com", password="pw")


@pytest.mark.django_db
def test_email_field_meta_is_unique():
    """Belt-and-braces: catch a future model edit that drops `unique=True`
    even if it's accompanied by a faulty migration that doesn't tear the
    DB constraint down. The model-level flag is what `full_clean()` and
    admin form validation rely on."""
    User = get_user_model()
    field = User._meta.get_field("email")
    assert field.unique is True
