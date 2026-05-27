from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

class StaticStorage(S3Boto3Storage):
    """
    Handles static files (CSS, JS, images).
    Stored in: bucket/project_folder/static/

    Static files must be overwritable by collectstatic so deployed
    updates actually reach the CDN.  A shorter Cache-Control (5 min)
    ensures stale assets don't stick around after a deploy.
    """
    location = settings.STATIC_LOCATION
    default_acl = "public-read"
    file_overwrite = True

    object_parameters = {
        "CacheControl": "public, max-age=300",
    }

class PublicMediaStorage(S3Boto3Storage):
    """
    Handles public uploads (user avatars, post images).
    Stored in: bucket/project_folder/media/
    """
    location = settings.PUBLIC_MEDIA_LOCATION
    default_acl = "public-read"
    file_overwrite = False

class PrivateMediaStorage(S3Boto3Storage):
    """
    Handles sensitive files (documents, private videos).
    Stored in: bucket/project_folder/private/
    """
    location = settings.PRIVATE_MEDIA_LOCATION
    default_acl = "private"
    file_overwrite = False
    # Crucial: Private files must bypass the CDN to use Signed URLs
    custom_domain = False


class ImportsStorage(S3Boto3Storage):
    """
    Handles company import .xlsx files.
    Stored in: bucket/project_folder/imports/
    Objects are private and short-lived (deleted on COMPLETED or purged by retention task).
    """
    location = settings.IMPORTS_LOCATION
    default_acl = "private"
    file_overwrite = False
    # Must bypass CDN so presigned URLs use the S3/Spaces endpoint directly.
    custom_domain = False
