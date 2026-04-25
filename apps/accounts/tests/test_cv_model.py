"""Tests for the CV model and its relationship with User.active_cv."""
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.accounts.models import CV


@pytest.mark.django_db
def test_user_can_have_multiple_cvs(user):
    cv1 = CV.objects.create(user=user, file=SimpleUploadedFile("a.pdf", b"a"), name="A")
    cv2 = CV.objects.create(user=user, file=SimpleUploadedFile("b.pdf", b"b"), name="B")
    assert user.cvs.count() == 2
    assert set(user.cvs.values_list("name", flat=True)) == {"A", "B"}
    assert cv1.pk != cv2.pk


@pytest.mark.django_db
def test_has_cv_returns_false_when_no_active_cv(user):
    assert user.has_cv is False


@pytest.mark.django_db
def test_has_cv_returns_true_when_active_cv_set(user):
    cv = CV.objects.create(user=user, file=SimpleUploadedFile("c.pdf", b"c"))
    user.active_cv = cv
    user.save(update_fields=["active_cv"])
    assert user.has_cv is True


@pytest.mark.django_db
def test_deleting_user_deletes_their_cvs(user):
    CV.objects.create(user=user, file=SimpleUploadedFile("x.pdf", b"x"))
    assert CV.objects.filter(user=user).count() == 1
    user.delete()
    assert CV.objects.count() == 0


@pytest.mark.django_db
def test_deleting_active_cv_nullifies_user_active_cv(user):
    cv = CV.objects.create(user=user, file=SimpleUploadedFile("y.pdf", b"y"))
    user.active_cv = cv
    user.save(update_fields=["active_cv"])
    cv.delete()
    user.refresh_from_db()
    assert user.active_cv is None
