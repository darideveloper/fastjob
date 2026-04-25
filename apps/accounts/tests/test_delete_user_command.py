"""Tests for the `delete_user` management command (GDPR tooling)."""
import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.accounts.models import CV


@pytest.mark.django_db
def test_delete_user_removes_account_and_cvs(user):
    CV.objects.create(user=user, file=SimpleUploadedFile("x.pdf", b"x"))
    User = get_user_model()
    call_command("delete_user", email=user.email, yes=True)
    assert not User.objects.filter(pk=user.pk).exists()
    assert CV.objects.filter(user_id=user.pk).count() == 0


@pytest.mark.django_db
def test_delete_user_errors_on_unknown_email(db):
    with pytest.raises(CommandError):
        call_command("delete_user", email="nobody@example.com", yes=True)
