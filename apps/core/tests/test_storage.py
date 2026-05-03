from django.test import TestCase, override_settings
from django.core.files.storage import storages
from apps.accounts.models import CV, User
from django.core.files.base import ContentFile
import os

class PrivateStorageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(email="test@test.com")

    @override_settings(STORAGE_AWS=True)
    def test_private_storage_acl(self):
        # Create a CV instance which uses private storage
        cv = CV.objects.create(user=self.user)
        cv.file.save("test.txt", ContentFile("test content"))
        
        # Verify it uses the private backend
        self.assertEqual(cv.file.storage.location, "fastjob/private/cvs/")
        
        # Verify default ACL is private
        storage = storages["private"]
        self.assertEqual(storage.default_acl, "private")

    def test_signed_url_generation(self):
        # We need a path to a file
        from apps.core.storage_utils import get_private_file_url
        url = get_private_file_url("fastjob/private/test.txt")
        self.assertIn("X-Amz-Signature", url)
