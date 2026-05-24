"""H10 regression: destructive flows are wrapped in transaction.atomic().

The acceptance criterion: "simulated kill mid-loop leaves either all CVs
deleted or none — no partial state." We simulate the kill by injecting an
exception inside the destructive block and assert that no rows changed.
"""
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.accounts.models import CV


@pytest.mark.django_db
def test_delete_account_rolls_back_on_midflight_failure(client, user_with_cv):
    """If something raises after some CVs have been deleted but before
    user.delete() commits, the whole delete must roll back. Without the
    atomic block, the user would still exist but be missing CVs."""
    User = get_user_model()
    # Add two more CVs so we have 3 to iterate over.
    CV.objects.create(user=user_with_cv, file=SimpleUploadedFile("b.pdf", b"x"), name="b")
    CV.objects.create(user=user_with_cv, file=SimpleUploadedFile("c.pdf", b"x"), name="c")
    initial_cv_count = user_with_cv.cvs.count()
    assert initial_cv_count == 3

    client.force_login(user_with_cv)

    # Inject failure on the LAST step — `user.delete()`. By that point the
    # CV loop has already removed (or attempted to remove) some rows; the
    # atomic block must undo them.
    original_delete = User.delete

    def failing_user_delete(self, *args, **kwargs):
        # Run the real cascade-delete first so we're testing rollback of
        # work that actually touched the DB, then explode.
        original_delete(self, *args, **kwargs)
        raise RuntimeError("simulated SIGTERM after partial work")

    with patch.object(User, "delete", failing_user_delete):
        with pytest.raises(RuntimeError, match="simulated SIGTERM"):
            client.post(
                reverse("delete_account"),
                {"confirm_email": user_with_cv.email},
            )

    # The atomic block rolled back: user still exists, all CVs still exist.
    user_with_cv.refresh_from_db()
    assert user_with_cv.cvs.count() == initial_cv_count
    assert User.objects.filter(pk=user_with_cv.pk).exists()


@pytest.mark.django_db
def test_delete_cv_rolls_back_active_cv_fallback_on_failure(client, user_with_cv):
    """delete_cv has two writes: removing the row + repointing active_cv.
    A crash between them used to leave active_cv pointing at a deleted PK.
    With atomic(), both land or neither does."""
    # Guard blocks deletion while campaign is active — pause first.
    user_with_cv.is_campaign_active = False
    user_with_cv.save(update_fields=["is_campaign_active"])
    cv2 = CV.objects.create(user=user_with_cv, file=SimpleUploadedFile("e.pdf", b"x"))
    target = user_with_cv.active_cv
    assert target is not None

    client.force_login(user_with_cv)

    # Patch User.save (called for the active_cv fallback) to raise. The
    # cv.delete() preceding it must roll back — otherwise we'd lose a CV
    # AND keep a stale active_cv pointer.
    original_save = type(user_with_cv).save

    def failing_save(self, *args, **kwargs):
        if kwargs.get("update_fields") and "active_cv" in kwargs["update_fields"]:
            raise RuntimeError("simulated DB error on fallback save")
        return original_save(self, *args, **kwargs)

    with patch.object(type(user_with_cv), "save", failing_save):
        with pytest.raises(RuntimeError, match="simulated DB error"):
            client.post(reverse("delete_cv", args=[target.pk]))

    # Rollback: target CV must still exist; active_cv unchanged.
    assert CV.objects.filter(pk=target.pk).exists()
    assert CV.objects.filter(pk=cv2.pk).exists()
    user_with_cv.refresh_from_db()
    assert user_with_cv.active_cv_id == target.pk
