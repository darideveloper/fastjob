# infrastructure — spec deltas

## ADDED Requirements

### Requirement: Object-Storage CORS Configuration for Imports
The object-storage bucket/space used for company-import files (selected via `STORAGES["imports"]` when `STORAGE_AWS=True`) SHALL have a CORS configuration that permits direct browser uploads from the production admin origin. The configuration MUST work identically on AWS S3 and DigitalOcean Spaces, since both implement the S3 `PutBucketCors` API.

The CORS rule MUST allow:
- `AllowedOrigins`: the production admin origin (e.g. `https://fastjob.apps.darideveloper.com`) and any staging origins
- `AllowedMethods`: `PUT`, `HEAD`
- `AllowedHeaders`: at minimum `Content-Type`, `Content-Length`, `x-amz-acl`
- `ExposeHeaders`: at minimum `ETag`
- `MaxAgeSeconds`: `3600` or higher

The bucket MUST NOT include `*` as `AllowedOrigins` (defense against signed-URL leaks being usable from third-party origins).

The application MUST provide a diagnostic check that verifies the CORS rule is in place by issuing a synthetic `OPTIONS` preflight with the production admin `Origin` header and asserting the response includes `Access-Control-Allow-Origin` and `Access-Control-Allow-Methods: PUT`. The check MUST be:
- Reachable via `manage.py check_company_import_storage` (extends the existing command)
- Surfaced in `/healthz` as a non-fatal warning when the CORS rule is missing or misconfigured

The CORS rule MUST be applied to the bucket *before* the new upload-page JavaScript is deployed, otherwise browser uploads silently fail. The cutover ordering is captured in the change's `tasks.md`.

#### Scenario: Production bucket has the CORS rule
- **GIVEN** the production imports bucket configured with the rule above
- **WHEN** an OPTIONS preflight is sent with `Origin: https://fastjob.apps.darideveloper.com` and `Access-Control-Request-Method: PUT`
- **THEN** the response includes `Access-Control-Allow-Origin: https://fastjob.apps.darideveloper.com`
- **AND** the response includes `Access-Control-Allow-Methods: PUT`
- **AND** `manage.py check_company_import_storage` exits with status `0`

#### Scenario: Missing CORS rule fails the diagnostic check
- **GIVEN** a bucket without a CORS rule (or with an `AllowedOrigins` that does not match the production admin origin)
- **WHEN** `manage.py check_company_import_storage` runs
- **THEN** the command exits with a non-zero status
- **AND** stdout names the missing or incorrect CORS field
- **AND** `/healthz` includes a warning identifying the misconfigured CORS

#### Scenario: CORS works against AWS S3 and DO Spaces identically
- **GIVEN** the same CORS rule applied via `aws s3api put-bucket-cors --endpoint-url=$AWS_S3_ENDPOINT_URL ...`
- **WHEN** the bucket is hosted on either AWS S3 (no `endpoint-url`) or DigitalOcean Spaces (`endpoint-url=https://nyc3.digitaloceanspaces.com`)
- **THEN** the diagnostic check passes for both
- **AND** the same browser PUT works against both

## MODIFIED Requirements

### Requirement: Shared Imports Volume Between Web and Worker
The deployment topology SHALL provide a shared, writable filesystem path between the `web` (gunicorn) and `celery_worker` services for company-import file hand-off **only when `STORAGE_AWS = False`** (local development, integration test environments without object storage). When `STORAGE_AWS = True`, web and worker MUST NOT require any shared filesystem — the worker reads import files directly from object storage via streaming `GetObject` requests.

When `STORAGE_AWS = False`:
- The path MUST be the same on both services and resolvable via the `COMPANY_IMPORT_LOCAL_PATH` environment variable (default `/app/imports`)
- In Docker Compose deployments the path MUST be backed by a named volume (e.g. `imports_data`) mounted on both services
- In non-Docker deployments the path MUST be backed by a shared filesystem (NFS, EFS, or equivalent) such that a file written by `web` is readable by `celery_worker` within the time it takes the Celery task to start
- The application MUST refuse to start the celery worker (or surface a `/healthz` warning) if the path is missing, not a directory, or not writable

When `STORAGE_AWS = True`:
- Web and worker MAY run on entirely separate hosts with no shared storage
- The worker reads import files via the `imports` storage backend (`S3Boto3Storage`), which streams from object storage
- The `/healthz` and `manage.py check_company_import_storage` checks MUST NOT fail simply because no shared volume is present — they MUST instead verify the bucket is reachable, the credentials are valid, and the CORS rule is in place (covered by the `Object-Storage CORS Configuration for Imports` requirement)

#### Scenario: Production deployment with object storage requires no shared volume
- **GIVEN** a production deployment with `STORAGE_AWS = True` and the imports bucket properly configured
- **WHEN** the `web` and `celery_worker` services start with no `imports_data` volume mounted
- **THEN** both services start successfully
- **AND** `/healthz` reports green for the imports-storage check
- **AND** an end-to-end import (presign → browser PUT → trigger → worker download → parse) completes successfully

#### Scenario: Local-dev deployment without object storage still requires the shared volume
- **GIVEN** a local Docker Compose deployment with `STORAGE_AWS = False`
- **WHEN** the operator omits the `imports_data` volume mount
- **THEN** `/healthz` includes a warning identifying the missing imports path (existing behaviour preserved)
- **AND** `manage.py check_company_import_storage` exits non-zero (existing behaviour preserved)

#### Scenario: Path mismatch between web and worker is still detected in local-dev mode
- **GIVEN** `STORAGE_AWS = False` AND `web` has `COMPANY_IMPORT_LOCAL_PATH=/app/imports` AND `celery_worker` has `COMPANY_IMPORT_LOCAL_PATH=/srv/imports`
- **WHEN** an upload is attempted
- **THEN** the discrepancy is surfaced via the worker-side health check before processing fails opaquely on `FileNotFoundError` (existing behaviour preserved for local-dev)

#### Scenario: Production deployment with `STORAGE_AWS=True` but no bucket reachable
- **GIVEN** `STORAGE_AWS = True` AND the bucket credentials are wrong or the bucket does not exist
- **WHEN** `/healthz` is polled
- **THEN** the response includes a warning identifying the unreachable imports storage
- **AND** `manage.py check_company_import_storage` exits non-zero
