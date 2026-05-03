from django.core.files.storage import storages
import datetime

def get_private_file_url(file_path, expiration=300):
    """
    Generates a time-limited signed URL for a file stored in the 'private' storage.
    Default expiration is 5 minutes (300 seconds).
    """
    storage = storages["private"]
    # Boto3 backend provides this method to generate signed URLs
    return storage.bucket.meta.client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": storage.bucket_name,
            "Key": file_path,
        },
        ExpiresIn=expiration,
    )
