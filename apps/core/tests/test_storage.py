from django.test import TestCase
from unittest.mock import patch, MagicMock
from apps.accounts.models import CV, User, _private_storage

class PrivateStorageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(email="test@test.com")

    def test_private_storage_mapping(self):
        from django.core.files.storage import storages
        # Verify the CV model's file field uses the private storage helper
        storage_field = CV._meta.get_field("file").storage
        self.assertEqual(storage_field, storages["private"])

    def test_private_media_storage_properties(self):
        from config.storage_backends import PrivateMediaStorage
        # Verify PrivateMediaStorage configuration properties are correct
        self.assertEqual(PrivateMediaStorage.default_acl, "private")
        self.assertEqual(PrivateMediaStorage.location, "fastjob/private")
        self.assertFalse(PrivateMediaStorage.custom_domain)

    @patch("apps.core.storage_utils.storages")
    def test_signed_url_generation(self, mock_storages):
        mock_storage = MagicMock()
        mock_storage.bucket_name = "fastjob"
        mock_storage.bucket.meta.client.generate_presigned_url.return_value = (
            "https://nyc3.digitaloceanspaces.com/fastjob/private/test.txt?X-Amz-Signature=mock"
        )
        mock_storages.__getitem__.return_value = mock_storage

        from apps.core.storage_utils import get_private_file_url
        url = get_private_file_url("fastjob/private/test.txt")
        self.assertIn("X-Amz-Signature", url)

