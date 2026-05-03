# Proposal: Implement Private S3 Storage Integration

## Overview
Currently, the application uses a single global S3 storage configuration. This proposal introduces a differentiated storage architecture using `django-storages` to ensure all user-uploaded content (CVs, Company Excels) is treated as private, preventing public access and requiring administrative authentication for all file interactions.

## Architectural Changes
- Implement `PrivateMediaStorage` backend in `config/storage_backends.py`.
- Enforce `private` ACL and bypass CDN for all uploads.
- Securely serve files via signed URLs or administrative view proxies.
- Refactor `CompanyImportBatch` and CV models to utilize the new `private` storage backend.
