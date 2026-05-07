# Design: Fix Excel-import timeout

## Context
Operators upload company lists through `/admin/companies/company/import-xlsx/`. The admin form has a JS-driven `XMLHttpRequest` that POSTs the multipart payload, then transitions the UI to "Guardando en el servidor…" once `xhr.upload.loadend` fires. The server-side handler is `CompanyAdmin.import_xlsx_view` in `apps/companies/admin.py`. The handler calls `CompanyImportBatch.objects.create(file=request.FILES["xlsx_file"])`, which — because `CompanyImportBatch.file` declares `storage=PrivateMediaStorage()` — synchronously uploads the file to DigitalOcean Spaces inside the request thread before the row INSERT.

Web and worker run as **separate Docker services** (`web` and `celery_worker` in `docker-compose.yml`), with no shared volume currently declared. The original async-import refactor (archived `2026-05-03-refactor-excel-import-async`) implicitly assumed remote storage was the file-handoff medium between web and worker; that assumption is the load-bearing flaw we are removing.

Stakeholders:
- **Operators** running imports — need uploads to complete or fail fast, with a clear message and a row visible in the import-batch list.
- **Platform/infra** — owns `docker-compose.yml`, gunicorn timeout, Coolify volume declarations, and disk-quota guarantees.
- **Backend developers** — own the `companies` app and the celery worker.

## Goals / Non-Goals

**Goals**
- Uploads of typical company files (≤25 MB) MUST return an HTTP redirect within seconds, never minutes.
- The `CompanyImportBatch` row MUST be visible in `/admin/companies/companyimportbatch/` for every upload attempt — successful, failing, and rejected — so operators have a paper trail.
- Worker MUST be able to read the uploaded file deterministically without depending on remote object storage.
- Disk usage on the shared volume MUST be bounded by an enforced retention policy, not unbounded growth.
- The fix MUST be safe to deploy under the existing Coolify-managed Docker Compose (the volume must be declared in a way that Coolify provisions per-deployment — see `${COOLIFY_VOLUME_*}` pattern already in use).

**Non-Goals**
- We will **not** introduce browser-direct presigned-POST uploads to S3. That is a strictly larger change (CORS on the bucket, presign endpoint, two-phase commit on the batch row, separate frontend) and is unnecessary for operator-only files of bounded size. It is captured in `Open Questions` for a future proposal.
- We will **not** change the public API of the importer (`import_companies_from_xlsx`).
- We will **not** keep long-term object-storage archival of import files. These are operator inputs that have already been materialized into `Company` rows; archival can be re-added later if a real audit need emerges.
- We will **not** change the JS upload library (sticking with vanilla `XMLHttpRequest`).

## Decisions

### Decision 0: Relationship to existing `Private Storage Backend` requirement
- **What**: The `infrastructure` capability previously required that "All user-uploaded files MUST be stored in a private-access storage bucket" with the scenario explicitly naming "a user uploading a CV or **Company Excel**." This proposal MODIFIES that requirement to scope it to end-user-uploaded PII (CVs and similar) and explicitly removes operator-uploaded company-import `.xlsx` files from its purview. Operator imports are governed instead by the `companies` capability spec and by the new `Shared Imports Volume Between Web and Worker` requirement.
- **Why**: The threat model behind the original requirement is PII protection — CVs contain personal data and must never leak. Operator company-import `.xlsx` files contain only the same business contact data that `/api/companies/count/` already exposes at aggregate level, and the file is operator-only input that exists transiently during one import run. Subjecting these files to the same private-S3-with-`private`-ACL mandate as CVs was an over-application of the rule and is what currently couples the import view to a slow remote-storage call. The privacy guarantee for CVs is preserved unchanged.
- **Alternatives considered**:
  1. Keep the existing requirement and route operator imports through the worker for the S3 upload (Path A in the audit). Rejected for this proposal because (a) the operator-import data has no PII risk; (b) it adds a multi-step state machine (`PENDING → STORED_LOCAL → ARCHIVED → PROCESSING → COMPLETED`) and a worker-side S3 transfer for files that we then immediately delete after processing on the success path; (c) the archival benefit is speculative — there is no current operator workflow that re-reads old import files.
  2. Leave the requirement unchanged and silently violate it. Rejected — `openspec validate` would not catch the conflict (it does not cross-check existing specs against new deltas), but human review would, and silent drift is exactly what OpenSpec is supposed to prevent.

### Decision 1: Local FileSystemStorage on a shared Docker volume
- **What**: A new named storage `imports` is registered in `STORAGES["imports"]`, backed by `django.core.files.storage.FileSystemStorage(location=settings.COMPANY_IMPORT_LOCAL_PATH)` (default `/app/imports`). `CompanyImportBatch.file`'s `storage` argument switches from `PrivateMediaStorage()` to a callable that returns the named-storage instance, so tests can override via Django's `override_settings`.
- **Why**: Local FS is the single fastest, most reliable hand-off between two co-located Docker services. It eliminates two failure modes simultaneously: boto3 retry storms in the request thread, and gunicorn worker timeouts caused by slow remote PUTs.
- **Alternatives considered**:
  1. **Keep `PrivateMediaStorage` but raise the gunicorn `--timeout`** beyond the proxy's upstream timeout. Rejected: it does not fix the underlying coupling; large files still hold a worker for minutes; it punishes the entire web tier for one slow path.
  2. **Stream the bytes through Redis**, with the worker pulling from Redis and writing to disk. Rejected: Redis is not a blob store; 25 MB payloads in Redis is wasteful and we already have a working broker on db 0 we don't want to bloat.
  3. **Browser → S3 presigned POST** (no Django bytes). Rejected for scope (see Non-Goals); the migration cost dwarfs the benefit for this internal-admin flow.
  4. **In-memory pickled bytes via Celery task argument**. Rejected: Celery task payloads are not designed for multi-MB blobs; broker memory pressure and replay cost are real risks.

### Decision 2: Three-step view ordering
- **What**: The admin view becomes:
  1. Validate form (size cap + extension).
  2. `batch = CompanyImportBatch.objects.create(status="PENDING")` — *no* file attached.
  3. Inside `try`: `batch.file.save(name, request.FILES["xlsx_file"], save=True)` (writes to local FS).
  4. On success: `process_company_import.delay(batch.id)`, redirect with success message.
  5. On `OSError` / `SuspiciousFileOperation`: set `batch.status = "FAILED"`, append error to `batch.error_log`, save, and redirect with an error message that names the batch ID.
- **Why**: This guarantees a visible row for every attempt. It also means the existing `CompanyImportBatchAdmin` is the single source of truth for "what just happened to my upload?", which is what an operator looking at `/admin/companies/companyimportbatch/` already expects.
- **Alternatives**: Wrapping the entire view in a single `try`/`except` around `objects.create(file=...)` does not give us the row when the storage write fails — losing the audit trail that motivated this change.

### Decision 3: Lifecycle — delete on success, keep on failure, sweep weekly
- **What**: `process_company_import` deletes the local file on `COMPLETED` (via `batch.file.delete(save=False)`). On `FAILED`, the file stays on disk, and `error_log` records its path. A new periodic task `purge_stale_company_import_files` runs daily (Celery Beat) and removes files whose batch's `created_at` is older than `COMPANY_IMPORT_FILE_RETENTION_DAYS` (default 7), regardless of status.
- **Why**: Successful imports do not need the source file — the `Company` rows are the artifact. Failed imports retain the file so an operator can download it from the admin and re-run after fixing the rows. The sweep bounds worst-case disk usage at `(retention_days × max_file_mb × max_imports_per_day)`.
- **Alternatives**: Keeping all files indefinitely was rejected — operators routinely import 5–15 MB files; without retention, disk grows monotonically.

### Decision 4: Form-level upload size cap (default 25 MB)
- **What**: `XlsxImportForm.clean_xlsx_file` rejects files larger than `settings.COMPANY_IMPORT_MAX_FILE_MB` MB. The HTML form and the JS pre-flight also surface the cap.
- **Why**: An operator uploading a multi-GB file by accident should fail at the gate, not after streaming 30 minutes of bytes.
- **Note**: Django's `FILE_UPLOAD_MAX_MEMORY_SIZE = 5 MB` controls the *spill-to-disk threshold*, not the *maximum*. We need an explicit cap. `DATA_UPLOAD_MAX_MEMORY_SIZE` does not apply to multipart file fields.

### Decision 4b: Deliberately NOT wrapping the upload view in `transaction.atomic`
- **What**: The admin upload view in `apps/companies/admin.py:import_xlsx_view` performs three independent SQL writes (create PENDING row → save file + update file name → optionally update to FAILED). These are NOT wrapped in `transaction.atomic`, even though doing so would close a microsecond-wide orphan-PENDING window where a gunicorn worker killed between INSERT and `file.save()` leaves a `PENDING` row with no file.
- **Why**: An atomic block would roll back the INSERT when the file write raises (`OSError` / `SuspiciousFileOperation`), violating the `Resilient Import Upload Pipeline` requirement that the view MUST persist a `CompanyImportBatch` row "for every upload attempt — including attempts where the file write fails." Atomic rollback erases the audit trail. Re-creating the row in the except branch defeats the point (different batch ID; race with the success-message redirect that already references the original ID).
- **How the orphan-PENDING risk is handled instead**: the periodic `purge_stale_company_import_files` task already iterates batches older than `COMPANY_IMPORT_FILE_RETENTION_DAYS` and clears stale files. A future small extension can also flip lingering `PENDING` rows older than e.g. 10 minutes to `FAILED` with an explanatory `error_log` entry. That preserves visibility AND eventually cleans up.
- **Alternatives considered**:
  1. `transaction.atomic` + recreate-on-except — rejected for the audit-trail reason above.
  2. `transaction.atomic` + `transaction.on_commit` for the file save — adds complexity and the same rollback hazard.
  3. Status quo (current implementation) — accepted; orphan-PENDING is bounded by the retention sweep.

### Decision 5: JS surfaces server-provided error messages
- **What**: When `xhr.status` is in `[400, 599]` and the response `Content-Type` is `application/json`, the JS reads `{"error": "..."}` from the body and displays that message instead of the generic localized string. The admin view returns those JSON bodies on the unhappy paths.
- **Why**: Operators should see "Archivo demasiado grande (35 MB > 25 MB)" rather than a flat alert. Keeps debugging cycles short.

## Alternative failure mechanisms to verify in logs

The confirmed failure mechanism is the gunicorn 300 s worker timeout (matches the user-reported "few minutes"). Two secondary mechanisms could co-exist or substitute and should be ruled out from logs before deploying:

- **boto3 retry storms** on a misconfigured Spaces endpoint. boto3's default `legacy` retry mode performs up to 5 attempts with exponential backoff on transient errors (connect resets, throttles), which can stretch a single PUT to several minutes — long enough to hit the same 300 s gunicorn ceiling. Symptom: `EndpointConnectionError` / `ConnectTimeoutError` / `ReadTimeoutError` in the Django log, possibly preceded by retry attempts.
- **Endpoint / region / bucket mismatch.** If `AWS_S3_ENDPOINT_URL` and `AWS_S3_REGION_NAME` disagree, or the bucket does not exist on that endpoint, boto3 surfaces a `ClientError` with status 403 / 404 — usually fast, not "few minutes." Worth a quick eyeball but unlikely to be the load-bearing cause given the timing.

If logs show neither mechanism, the gunicorn-timeout diagnosis stands and the architectural fix in Decision 1 still applies — the import path simply should not be on the request thread regardless of which specific failure variant trips first.

## Risks / Trade-offs

- **Risk**: Shared Docker volume not provisioned in a particular Coolify deployment → web writes a file the worker cannot read, the task fails immediately with `FileNotFoundError`.
  **Mitigation**: Add a `manage.py check_company_import_storage` management command that the worker runs at boot to verify the path is mounted, writable, and visible. The `/healthz` endpoint also surfaces this.
- **Risk**: Disk fills up because operators upload aggressively or the sweep is broken.
  **Mitigation**: Retention sweep has its own log line + Sentry breadcrumb. `imports_data` volume is sized in compose. Alarm threshold is the operator's monitoring concern (out of scope here).
- **Risk**: `BREAKING` for non-Docker / multi-host deployments where web and worker do not share a filesystem.
  **Mitigation**: `design.md` and the spec delta call this out explicitly. In such deployments, the path can be backed by an NFS / EFS mount; this proposal does not prescribe how, only that it must be shared.
- **Trade-off**: We are dropping S3 archival of import files. If that turns out to be needed for compliance, a follow-up proposal can re-add a "post-process upload to Spaces" step in the celery task.

## Migration Plan

1. **Pre-deploy**: Verify no in-flight `CompanyImportBatch` rows are in `PENDING`/`PROCESSING`. Because the bug prevents any from succeeding, the table is currently empty in affected environments — trivially safe.
2. **Deploy order**:
   1. Update `docker-compose.yml` to declare `imports_data` and mount `/app/imports` on both `web` and `celery_worker`. Roll out infra change first (no code change yet).
   2. Deploy the code change. New uploads use local storage immediately.
3. **Backfill**: Not applicable — no existing successful batch files.
4. **Rollback**: Revert the code commit. The volume can stay (idempotent); old code will resume writing to Spaces. No data loss because import files are not authoritative state.

## Open Questions
- Do we want to expose the local file as a downloadable link in the `CompanyImportBatchAdmin` for `FAILED` batches? Probably yes for operator convenience; out of scope for this change but tracked.
- Should we add multi-host support via an S3 fallback storage when no shared filesystem is available? Defer until a non-Docker deployment exists.
- Should browser-direct presigned-POST be the long-term answer once non-admin users can upload files? Tracked for a future capability proposal; not blocking.
