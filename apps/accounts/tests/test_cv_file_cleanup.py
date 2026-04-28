"""C9 regression tests: the S3 object underlying a CV.file MUST be deleted
in every code path that removes the row.

Before the fix, only `CV.delete()` (single-instance) cleaned up — `User.delete()`
cascade and `QuerySet.delete()` (admin bulk-delete) silently leaked orphan
objects into the Spaces bucket. The fix replaces the model `delete()` override
with a `pre_delete` signal receiver, which Django fires for ALL three paths.

We mock `FieldFile.delete` rather than touching real storage so the assertion
is "the receiver actually invoked the storage delete", not "the test setup
configured storage correctly".
"""
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.accounts.models import CV


@pytest.fixture
def user_with_three_cvs(user):
    cvs = [
        CV.objects.create(user=user, file=SimpleUploadedFile(f"{i}.pdf", b"x"), name=f"cv{i}")
        for i in range(3)
    ]
    return user, cvs


@pytest.mark.django_db
def test_single_cv_delete_drops_storage_object(user_with_three_cvs):
    _, cvs = user_with_three_cvs
    target = cvs[0]
    with patch("django.db.models.fields.files.FieldFile.delete") as mock_delete:
        target.delete()
    assert mock_delete.call_count == 1
    # `save=False` is critical: saving here would re-INSERT the row we're
    # mid-deleting and crash the SQL transaction.
    mock_delete.assert_called_with(save=False)


@pytest.mark.django_db
def test_user_delete_cascade_drops_all_cv_storage_objects(user_with_three_cvs):
    """The bug C9 fixes: `User.delete()` cascades to CV rows but did NOT
    fire the override, so files stayed in the bucket. With `pre_delete`,
    each cascade-deleted CV triggers exactly one file.delete()."""
    user, _ = user_with_three_cvs
    with patch("django.db.models.fields.files.FieldFile.delete") as mock_delete:
        user.delete()
    assert CV.objects.count() == 0
    assert mock_delete.call_count == 3


@pytest.mark.django_db
def test_queryset_bulk_delete_drops_all_cv_storage_objects(user_with_three_cvs):
    """The other half of C9: admin bulk-delete (and any direct
    `CV.objects.filter(...).delete()`) calls QuerySet.delete(), which
    skips Model.delete() entirely. `pre_delete` still fires per row."""
    user, _ = user_with_three_cvs
    with patch("django.db.models.fields.files.FieldFile.delete") as mock_delete:
        CV.objects.filter(user=user).delete()
    assert CV.objects.count() == 0
    assert mock_delete.call_count == 3
