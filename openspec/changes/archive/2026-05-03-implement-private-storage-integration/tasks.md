# Tasks: Private Storage Integration

- [x] Create `config/storage_backends.py` defining `StaticStorage`, `PublicMediaStorage`, and `PrivateMediaStorage` classes.
- [x] Configure `config/settings.py` to support `STORAGE_AWS` environment variable and map the Django `STORAGES` engine.
- [x] Implement `AWS_PROJECT_FOLDER` logic in `settings.py` for storage location isolation.
- [x] Update `CompanyImportBatch` and CV models to utilize the `private` storage alias.
- [x] Implement administrative utility to generate time-limited S3 signed URLs for `private` files.
- [x] Add tests to verify file access control (ensure `private` ACL files are not publicly accessible).
- [x] Update `Dockerfile` to include `ARG` and `ENV` variables for S3 during build time as per documentation.
