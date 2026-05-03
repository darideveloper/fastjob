# Design: Secure Private Storage Architecture

## Strategy
1. **Infrastructure**: Implement `config/storage_backends.py` with three backends: `StaticStorage`, `PublicMediaStorage`, and `PrivateMediaStorage` inheriting from `S3Boto3Storage`.
2. **Access Control**: Set `default_acl = "private"` for `PrivateMediaStorage` to ensure sensitive content (CVs, Company Excels) is never publicly accessible.
3. **Settings Integration**: Update `config/settings.py` to use a `STORAGE_AWS` environment variable toggle, mapping backends via the `STORAGES` dictionary (Django 4.2+ standard).
4. **Environment Isolation**: Utilize `AWS_PROJECT_FOLDER` in `settings.py` to map storage locations (`{AWS_PROJECT_FOLDER}/private`, etc.), ensuring strict path isolation.
5. **Admin Secure Access**: Implement administrative view utilities for retrieving time-limited signed URLs, bypassing public CDN domain access for private files.
