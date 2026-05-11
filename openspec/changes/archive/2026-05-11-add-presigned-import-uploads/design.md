# Design: add-presigned-import-uploads

## Context

The current upload path:

```
Browser ──multipart POST──▶ Traefik ──proxy──▶ gunicorn ──MultiPartParser──▶ Django view
                                                                          ──▶ FileField.save() ──▶ FileSystemStorage (Docker volume)
                                                                          ──▶ Celery dispatch
Celery worker ──read──▶ Docker volume ──parse──▶ Postgres
```

Every arrow upstream of "Celery dispatch" buffers, copies, or counts the file body. The proposed path:

```
Browser ──small JSON POST──▶ Django (presign endpoint) ──signed URL──▶ Browser
Browser ──direct PUT──▶ Object storage (S3 / Spaces)              [skips Traefik + gunicorn]
Browser ──small JSON POST──▶ Django (trigger endpoint) ──key──▶ CompanyImportBatch row
                                                              ──▶ Celery dispatch
Celery worker ──streaming GET──▶ Object storage ──parse──▶ Postgres
```

The Django request bodies are now bounded to ~1 KB regardless of `.xlsx` size.

## Decisions and Rationale

### D1. Provider abstraction: one boto3 client, two endpoints

DigitalOcean Spaces is S3-API-compatible. The existing `S3Boto3Storage` backend (django-storages) already works against both — the only difference is `AWS_S3_ENDPOINT_URL` (Spaces) vs unset (AWS). Presigned URLs use the standard SigV4 signature; both providers accept identical PUT calls with `Content-Type` and `Content-Length` headers.

There are exactly three differences worth pinning down in implementation:

| Concern | AWS S3 | DigitalOcean Spaces |
|---|---|---|
| Signature region | Required for sig (e.g. `eu-west-1`) | Region matches the Spaces region, e.g. `nyc3` (already set via `AWS_S3_REGION_NAME`) |
| URL style | Virtual-hosted (`<bucket>.s3.<region>.amazonaws.com`) | Virtual-hosted (`<bucket>.<region>.digitaloceanspaces.com`) — same shape |
| CORS API | `PutBucketCors` (S3 standard) | `PutBucketCors` (S3 standard, identical request shape) |

**Decision**: Use `boto3.client("s3", endpoint_url=settings.AWS_S3_ENDPOINT_URL or None, region_name=settings.AWS_S3_REGION_NAME, ...)`. When `AWS_S3_ENDPOINT_URL` is empty, boto3 falls back to AWS S3. No conditional code branches based on provider.

### D2. CORS configuration is operator-managed, not application-managed

The bucket's CORS rules must be set out-of-band (DO Spaces dashboard / AWS S3 console / `aws s3api put-bucket-cors`). The application MUST NOT attempt to mutate bucket policy at runtime — that requires escalated IAM permissions and is a one-time setup.

Required CORS rule (apply both providers):

```json
[
  {
    "AllowedOrigins": ["https://fastjob.apps.darideveloper.com"],
    "AllowedMethods": ["PUT", "HEAD"],
    "AllowedHeaders": ["Content-Type", "Content-Length", "x-amz-acl"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3600
  }
]
```

`check_company_import_storage` will probe this with a HEAD preflight using a synthetic Origin header and fail loudly if the rule is missing.

### D3. Presigned PUT, not POST policy

`generate_presigned_url("put_object", ...)` is simpler than `generate_presigned_post(...)`:

- PUT: one URL, browser does `XHR.open("PUT", url)` and `xhr.send(file)`. Single-shot.
- POST policy: returns a form spec; browser must build a FormData with named fields exactly matching the policy. More moving parts.

PUT works identically on AWS and DO Spaces. POST policy has known DO Spaces edge cases around field ordering. **Decision**: PUT.

The signed URL includes `Content-Type` and `Content-Length` as signed headers. The browser MUST send the matching values, which gives us a server-enforced size cap (the upload to S3 will fail with `403 SignatureDoesNotMatch` if the browser tries to send more bytes than the presigned `Content-Length`).

### D4. Object key shape: `imports/<batch-uuid>/<sanitized-filename>.xlsx`

Why include the original filename:

- Operator-readable in the S3 console
- `error_log` entries that name the file remain meaningful
- Diagnostic value when an import fails and the file is retained

Why UUID-prefix it:

- Prevents collisions when the same operator uploads two files with the same name
- Eliminates the entire class of object-key injection attacks (the operator never picks the prefix)
- Lifetime of the object is tied to the batch row

Filename sanitisation: NFKD-normalise + strip non-ASCII + collapse whitespace + truncate to 64 chars. `Copy of BBDDESPAÑA-575.xlsx` becomes `Copy_of_BBDDESPANA-575.xlsx`. The raw original is preserved in `CompanyImportBatch.original_filename` (new field) for display.

### D5. Streaming reads in the Celery task

Current code: `_preflight_total_rows(batch.file.path)` and `load_workbook(batch.file.path, ...)`. The `.path` attribute does not exist on `S3Boto3Storage`. Two options:

| Option | Pros | Cons |
|---|---|---|
| Download to `NamedTemporaryFile`, pass path | Minimal change to import code; openpyxl already happy with paths | Worker disk usage; requires explicit cleanup |
| Stream via `batch.file.open("rb")` | No temp file; no cleanup | openpyxl `load_workbook(file_like)` works but spends 2-3× memory because it can't seek efficiently |

**Decision**: Download to a `NamedTemporaryFile(delete=True)` inside the task, pass `tmp.name` to existing parser code. The temp file lives only during the parse and is cleaned up on task exit. This minimises change to `_preflight_total_rows`, `load_workbook`, and the row iterator. The `try/finally` already in the task is the natural cleanup point.

### D6. Backwards compatibility: `STORAGE_AWS=False` keeps the local volume

For `manage.py runserver` developers, requiring a real bucket would add friction with no benefit. The `STORAGES["imports"]` mapping branches on `STORAGE_AWS`:

- `STORAGE_AWS=True` (production, staging, CI integration tests): `ImportsStorage(S3Boto3Storage)` against `AWS_STORAGE_BUCKET_NAME`/`imports/` prefix.
- `STORAGE_AWS=False` (local dev): `FileSystemStorage` against `COMPANY_IMPORT_LOCAL_PATH` — exactly today's behaviour.

The view, model, and task code never branch on `STORAGE_AWS`. They always go through the same `_imports_storage()` helper. Only the storage backend differs.

The `infrastructure` spec's "Shared Imports Volume Between Web and Worker" requirement is **narrowed**, not removed: it applies only when `STORAGE_AWS=False`. Production no longer needs the volume.

### D7. Upload size cap is now a JSON-validated number, not a multipart byte count

Old: form's `clean_xlsx_file` checks `f.size > max_bytes` after Django has buffered the body.

New: presign endpoint receives `{"filename": "...", "content_length": <int>, "content_type": "..."}`. It validates:

1. `content_length <= COMPANY_IMPORT_MAX_FILE_MB * 1024 * 1024`
2. `filename.lower().endswith(".xlsx")`
3. `content_type` is one of the allowed Excel MIME types
4. Operator is admin (`self.admin_site.admin_view`)

Then it generates the presigned URL with `Content-Length: <content_length>` baked in. The browser must send exactly that many bytes; if it sends more, S3 rejects with `403`. If it sends less, S3 rejects with `403` too (signature mismatch). Defense in depth: even a malicious admin can't bypass the cap by lying.

### D8. Trigger endpoint: validate the key shape, not the file content

The existing `import_xlsx_view` becomes a `POST` accepting `{"key": "imports/<batch-uuid>/<filename>"}`. Validation:

1. Key matches the regex `^imports/[0-9a-f-]{36}/[A-Za-z0-9_.-]+\.xlsx$`
2. `storage.exists(key)` returns True
3. The file size at that key is ≤ the cap (cheap `HeadObject`)
4. The batch UUID embedded in the key is not already claimed by another `CompanyImportBatch` row

Steps 2 and 3 prevent an admin from triggering an import on a key that doesn't exist or is bogus. Step 4 prevents replay (multiple POSTs of the same key creating multiple batches racing on the same file).

### D9. Failure-mode mapping

| Failure | Surface | UI message |
|---|---|---|
| Presign endpoint receives oversize `content_length` | `400` JSON | "El archivo excede el límite de N MB" |
| Browser PUT to S3 fails (CORS, network, signature) | XHR `error` callback | "Error al subir el archivo a la nube. Revisa tu conexión." |
| Trigger receives a key that doesn't exist | `400` JSON | "La subida no se completó. Vuelve a intentarlo." |
| Trigger receives a key whose `HeadObject` reports oversize | `400` JSON | "El archivo subido excede el límite de N MB" |
| Trigger receives a key already claimed by a batch | `409` JSON | "Esta subida ya fue procesada." |

All five are recoverable; the operator retries. None of them produces a 502 or a silent fallback.

### D10. CSP / mixed content

Browser PUTs to `https://<bucket>.<region>.digitaloceanspaces.com/...` (or `https://<bucket>.s3.<region>.amazonaws.com/...`). Both endpoints are HTTPS, so no mixed-content issue. The admin's existing CSP (if any) needs `connect-src` extended to include the storage hostname; this is captured as a task.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| CORS misconfigured silently breaks uploads in browser only (curl works) | `check_company_import_storage` performs a synthetic OPTIONS preflight and fails on missing CORS headers |
| Operator deletes the bucket / changes ACL out-of-band | `_imports_storage` exposes a probe used by `/healthz`; missing bucket flips the worker's healthcheck |
| Presigned URLs leak via referer or browser history | Expiry kept short (`COMPANY_IMPORT_PRESIGN_EXPIRY_SECONDS`, default 600s); URL never appears in a navigation bar (XHR only, never `<a href>`) |
| Concurrent uploads with same UUID (race) | Database-side `unique=True` on a future `CompanyImportBatch.upload_uuid` field, OR generate UUID server-side as part of the presign response (preferred — no client-side UUID needed) |
| Object-storage egress costs | Imports happen rarely (admin-driven). Bandwidth is bounded by `COMPANY_IMPORT_MAX_FILE_MB × imports/month`. Negligible at expected volume. |
| AWS / DO outage | Same as today's media-CV path. The `imports` storage failure mode is identical to existing `default` and `private` storage failures, which already exists in the threat model. |

## Alternatives Considered

- **tus.io chunked uploads**: rejected. More code, no benefit at our file sizes.
- **Multipart S3 upload from day 1**: rejected. Adds JS complexity (init/part/complete dance) for files where single-PUT works fine. Captured as a follow-up if file sizes regularly exceed 100 MB.
- **Drop file into Docker volume via SCP + admin button**: viable for small ops teams (Option G in the chat) but doesn't generalise to non-technical operators and doesn't remove the underlying volume requirement.
- **Switch gunicorn to a non-WSGI server (uvicorn/granian)**: solves the worker-hold problem but not the proxy-buffer / body-limit / OOM problems. Doesn't address root cause.

## What Stays the Same

- `CompanyImportBatch` model fields (file, status, counters, error_log, timestamps) — only the `file` field's underlying storage swaps
- `process_company_import` Celery task — the parse logic, chunked transactions, blacklist normalisation, progress reporting, retention semantics — all untouched. Only the file-open call changes
- `purge_stale_company_import_files` — same retention window, same per-row logic; iterates the storage layer's listing API instead of `os.scandir`
- Admin progress widget, the polling JSON endpoint, the `Live Progress Dashboard` requirement — untouched
- All blacklist normalisation, taxonomy resolution, lowercase semantics — untouched
- The `Enhanced Spanish XLSX Importer` requirement — untouched

The blast radius is the upload mechanism, not the import logic.
