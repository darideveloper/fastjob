# Excel Upload & Processing — Audit, Bugs, and Required Fixes

Scope: the "Importar empresas desde Excel" feature in the admin. This audit
covers the full chain: HTTP upload → file storage → Celery task → row
extraction → DB write → admin progress UI.

Files inspected:

- `apps/companies/admin.py` — `XlsxImportForm`, `import_xlsx_view`
- `apps/companies/importers.py` — `import_companies_from_xlsx`
- `apps/companies/tasks.py` — `process_company_import`
- `apps/companies/models.py` — `CompanyImportBatch`
- `templates/admin/companies/import_xlsx.html` — upload UI
- `config/settings.py` — `STORAGE_AWS`, `STORAGES`
- `config/storage_backends.py` — `PrivateMediaStorage`
- `apps/companies/tests/test_importers.py`, `test_tasks.py`

---

## Goal (from the user)

1. Upload the file to Django (fast, just receive bytes locally).
2. In **background**, upload the file to remote storage (S3 / DO Spaces).
3. In **background**, parse the Excel and persist Company rows.
4. **Per-row resilience**: if a row fails to extract / save, log the error
   and continue with the next row — never abort the whole import.
5. **Dashboard visibility**: the admin must show progress (current step,
   processed lines, total lines, etc.).

---

## Current flow (as implemented today)

1. User submits the admin form.
2. `import_xlsx_view` calls
   `CompanyImportBatch.objects.create(file=request.FILES["xlsx_file"])`.
   - Because `CompanyImportBatch.file` declares
     `storage=PrivateMediaStorage()`, the request thread uploads the file
     to S3 **synchronously** while the user waits.
3. `process_company_import.delay(batch.id)` enqueues the Celery task.
4. The Celery worker re-downloads the file from S3 into a `NamedTemporaryFile`
   (loading the whole thing into memory), then calls
   `import_companies_from_xlsx(tmp.name)`.
5. The importer wraps **every row** in a single `transaction.atomic()` block,
   does only minimal validation (email + empresa), and writes via
   `update_or_create`.

This violates goals #2 (S3 upload is in the request thread, not background)
and #4 (any DB-level error in any row aborts everything).

---

## Bugs & issues (ranked by severity)

### 🔴 Critical

#### B1. Single `transaction.atomic()` defeats per-row resilience

`importers.py:41` wraps the whole row loop in `transaction.atomic()`.
Inside the loop only `email`/`name` are validated; anything else
(`Area.get_or_create`, `Location.get_or_create`,
`Company.update_or_create`) can raise `IntegrityError`,
`DataError`, etc. When that happens the whole transaction rolls
back — every previously-imported row is lost, and the task ends up
in `FAILED`. This directly contradicts requirement #4.

**Fix:** wrap **each row** in its own `transaction.atomic()` and
catch `Exception` per row, appending a structured error to the log
and continuing the loop.

```python
for row_num, row in enumerate(rows_iter, start=2):
    try:
        with transaction.atomic():
            ... # extract + upsert
    except Exception as exc:
        errors.append(f"Fila {row_num}: {exc}")
        continue
```

#### B2. S3 upload happens in the HTTP request, not in background

`admin.py:67` calls `CompanyImportBatch.objects.create(file=...)` which,
because of `PrivateMediaStorage`, streams the upload to S3/Spaces during
the request. For multi-MB Excel files on a slow uplink this blocks the
admin user, defeats the JS progress bar, and risks gunicorn worker
timeouts (`upstream timed out` / 502).

**Fix:** save the file locally first (e.g. to `MEDIA_ROOT/imports/incoming/`
via a separate `FileField` with `FileSystemStorage`, or to a temp dir),
return immediately, and have a **first** Celery task `upload_import_to_remote`
move the bytes to S3 and update the batch. Only then chain
`process_company_import`.

A clean shape:

```
ImportBatch.local_file  -> FileSystemStorage (always)
ImportBatch.remote_file -> PrivateMediaStorage (set after upload task)

view  -> save local_file -> chain(upload_to_remote.s(id), process.s())
```

#### B3. `PrivateMediaStorage()` is instantiated at import time, even when `STORAGE_AWS=False`

`models.py:109`:
```python
file = models.FileField(upload_to="imports/companies/", storage=PrivateMediaStorage())
```
`PrivateMediaStorage` extends `S3Boto3Storage` and resolves
`settings.PRIVATE_MEDIA_LOCATION` on instantiation. When
`STORAGE_AWS=False`, that setting is **not defined** (see
`settings.py:177-209`), and even if it were, the backend would still try
to talk to S3 in environments without AWS credentials (e.g. local dev,
CI). It will surface as `AttributeError: 'Settings' object has no
attribute 'PRIVATE_MEDIA_LOCATION'` or boto auth errors.

**Fix:** use the `storages["private"]` alias instead, and let the
`STORAGES` mapping decide the backend:
```python
from django.core.files.storage import storages
file = models.FileField(
    upload_to="imports/companies/",
    storage=lambda: storages["private"],
)
```
…or accept `storage` as a callable returning the named storage. With B2
adopted, the user-facing `file` field becomes local-only and this whole
hazard goes away.

#### B4. No total/processed counters → no real progress visible

`CompanyImportBatch` only stores `status`, `created_count`,
`updated_count`, `error_log`. There is **no** `total_rows`,
`processed_rows`, `current_step`, or `upload_progress`. The admin
list (`CompanyImportBatchAdmin`) therefore cannot show progress; the
user only sees `PROCESSING` until the task ends.

**Fix:** add fields:

```python
total_rows         = PositiveIntegerField(default=0)
processed_rows    = PositiveIntegerField(default=0)
error_count       = PositiveIntegerField(default=0)
step              = CharField(choices=[
    ("UPLOADED_LOCAL", "Subido al servidor"),
    ("UPLOADING_REMOTE", "Subiendo a almacenamiento remoto"),
    ("UPLOADED_REMOTE", "Subido a almacenamiento remoto"),
    ("PARSING", "Procesando filas"),
    ("DONE", "Finalizado"),
])
started_at, finished_at = DateTimeField(null=True, blank=True)
```

Update `processed_rows` periodically (e.g. every 50 rows) inside the
importer so the admin list reflects real progress. Add a `progress_pct`
property and surface it in `list_display`. Optionally add an admin
detail view that auto-refreshes via meta-refresh or HTMX poll.

---

### 🟠 High

#### B5. `tmp.write(f.read())` loads the whole file into memory

`tasks.py:24` reads the entire S3 object into RAM. A 200 MB Excel file
becomes 200 MB of resident memory in the Celery worker — and Excel
parsing on top of that easily OOMs small workers.

**Fix:** stream chunks:
```python
with batch.file.open("rb") as src:
    for chunk in iter(lambda: src.read(1024 * 1024), b""):
        tmp.write(chunk)
```
Or use `shutil.copyfileobj(src, tmp)`.

#### B6. No file-type / size validation on upload

`XlsxImportForm.xlsx_file` is a plain `FileField`. A user can upload a
500 MB `.zip` named `foo.xlsx`; it will hit S3 and the worker, then
crash inside `openpyxl.load_workbook` with a generic exception.

**Fix:** validate extension (`.xlsx` only) and `MAX_UPLOAD_SIZE` in
`XlsxImportForm.clean_xlsx_file()`, plus a magic-bytes check
(`zipfile.is_zipfile`) since `.xlsx` is a ZIP container.

#### B7. Importer aborts on missing headers without recording a batch error

When headers are missing, the importer returns `(0, 0, ["..."])`. The
task stores that in `error_log`, sets status `COMPLETED`, and returns
counts of zero. The admin row will look indistinguishable from a
successful but empty import. Status should be `FAILED` (or a new
`HEADERS_INVALID`) when `created+updated == 0` and headers were missing.

#### B8. `update_or_create` always overwrites optional fields with empty strings

If a re-import has empty `direccion` for an existing row, the existing
address is wiped to `""` (because `defaults` always includes the
truncated empty string). For an upsert-by-email tool that's used to
"top up" data, this is dangerous data loss.

**Fix:** strip empty values from `defaults` before passing them in:
```python
defaults = {k: v for k, v in defaults.items() if v not in ("", None)}
```
(and document this behavior). If overwriting is intentional, document
it explicitly in the admin help text.

#### B9. Race-prone `get_or_create` for Area/Location

Under concurrent imports, two workers can call
`Area.objects.get_or_create(name="x")` simultaneously and both attempt
INSERT, raising `IntegrityError` due to `unique=True` on `name`.
Combined with B1, this is one of the realistic ways to lose all rows.

**Fix:** wrap the get_or_create in a `try/except IntegrityError: refetch`
pattern, or use `bulk_create(..., ignore_conflicts=True)` for taxonomy
preloading from a deduped set computed before the row loop.

---

### 🟡 Medium

#### B10. Inconsistent docs / help_text vs. real columns

- `XlsxImportForm.help_text` says: `empresa, email, actividad, direccion, cp, poblacion, provincia, comunidad, telefono, fax, website`.
- `templates/admin/companies/import_xlsx.html` says: `name`, `email`, `area`, `location`.
- The importer actually reads Spanish headers (`empresa`, `actividad`, `poblacion`, …).

The template is **wrong** — `name` and `area` would not match
`EXPECTED_HEADERS = {"email", "empresa"}`. Users following the template
will get "Columnas requeridas faltantes: empresa".

**Fix:** rewrite the template's help block to mirror the form's
`help_text`, and consider centralizing the canonical column list in a
constant in `importers.py` and rendering it from there.

#### B11. Truncation can cause `Location` collisions

`location_name = get("poblacion").lower()[:200]` — `Location.name` is
`unique=True, max_length=200`. Two different locations that share the
first 200 chars become the same row. Unlikely but real for noisy data.
Same risk for `Area`.

**Fix:** if the source data is known clean, leave it; otherwise log a
warning when truncation actually changes the value.

#### B12. `error_log` overwrite vs. append (and unbounded size)

The task does `batch.error_log = errors` — fine for one run, but if the
task is retried (e.g. Celery `autoretry_for`), the prior errors are
lost. Also, `error_log` is a `JSONField(default=list)`; on a 50k-row
import with many bad rows it can balloon and slow down the admin
change-list page.

**Fix:** store a capped error tail (e.g. first 500 errors) plus the
total `error_count`. Optionally store a separate `ImportRowError`
table with FK to the batch so the admin can paginate.

#### B13. No `select_for_update` on retry / no idempotency

If the Celery task crashes mid-import (worker killed, OOM), the next
retry will start over from row 2 and re-`update_or_create` the rows —
fine for upserts, but the `created_count` becomes inaccurate (already-
inserted rows now count as updates). For pure idempotency, stamp a
`last_import_batch_id` on Company and skip rows already stamped with
the current batch.

#### B14. `wb.close()` is unreachable on exception

`importers.py:103` is after the `with transaction.atomic()` block but
before `return`. If the loop raises, `wb.close()` is skipped. With
`read_only=True` workbooks this is rarely fatal but still leaks a
mmapped file handle.

**Fix:** use `with openpyxl.load_workbook(...) as wb:` (openpyxl
supports the context manager) or wrap in `try/finally`.

#### B15. `ws.iter_rows` walks the active sheet only

`wb.active` returns the first sheet. Multi-sheet files silently skip
data. Either error out if more than one sheet has rows, or document the
limitation in the form help text.

---

### 🟢 Low / nice-to-have

#### B16. `lowercase_fields` mixin double-lowercases

The importer already lowercases `email`, `name`, etc. before calling
`update_or_create`. The mixin then lowercases again on save. Harmless,
but the duplication makes it easy to forget which layer is responsible.

#### B17. UI progress bar misleads the user

The template shows "Guardando en el servidor, por favor espera…" while
Django uploads to S3 synchronously. With B2 fixed the message becomes
accurate ("Subiendo al servidor", then redirect). Until then, the user
sees a frozen progress bar with no feedback during the multi-second S3
push.

#### B18. No admin link from batch row to its source file

`CompanyImportBatchAdmin` does not expose a download link for `file`,
which is useful for debugging "why did row 27 fail?".

#### B19. Tests do not cover the per-row failure path

`test_importers.py` only tests email validation failures (which the
current code does handle). There is **no test** for a row that crashes
inside `update_or_create` (e.g. via a `MaxLengthError` or
`IntegrityError`). Adding one would have caught B1.

#### B20. `CompanyImportBatch` lacks a `created_by` user FK

For audit, store the admin user who triggered the import.

---

## Required fixes — implementation plan

Order matters: do the model + storage changes first so subsequent code
has the fields it needs.

### Step 1 — Model changes (`apps/companies/models.py`)

- Add fields on `CompanyImportBatch`:
  `step`, `total_rows`, `processed_rows`, `error_count`,
  `started_at`, `finished_at`, `created_by` (FK User, optional).
- Replace `storage=PrivateMediaStorage()` with the `storages["private"]`
  named-storage alias, OR split into:
  - `local_file = FileField(upload_to="imports/incoming/", storage=...)`
  - `remote_file = FileField(upload_to="imports/companies/", storage=...,  null=True, blank=True)`
- Generate a migration.

### Step 2 — Admin upload view (`apps/companies/admin.py`)

- In `import_xlsx_view`, save the upload to **local** storage only.
- Set `step = "UPLOADED_LOCAL"`, `status = "PENDING"`.
- Enqueue a Celery chain:
  `upload_import_to_remote.s(batch.id) | process_company_import.s()`.
- Strengthen `XlsxImportForm` with extension + size + magic-bytes
  validation.

### Step 3 — Tasks (`apps/companies/tasks.py`)

- New task `upload_import_to_remote(batch_id)`:
  open `local_file`, stream-copy bytes to a `PrivateMediaStorage`-backed
  `remote_file`, update `step = "UPLOADED_REMOTE"`. On failure: status
  `FAILED`, append to `error_log`.
- Refactor `process_company_import(batch_id)`:
  - Set `step = "PARSING"`, stamp `started_at`.
  - Use `shutil.copyfileobj` to download to tempfile.
  - Pass `batch` (or a progress callback) to the importer so it can
    update `processed_rows` periodically.
  - On task exception, status `FAILED`, traceback in error_log, but DO
    NOT lose already-committed rows (because per-row atomic — see B1).
  - Stamp `finished_at`, `step = "DONE"`.

### Step 4 — Importer (`apps/companies/importers.py`)

- Compute `total_rows` first (`ws.max_row - 1`) and write it to the batch.
- Replace the outer `transaction.atomic()` with **per-row** atomic blocks
  inside a `try/except Exception` that appends to `errors` and
  `continue`s.
- Strip empty values from `defaults` (B8).
- Update `batch.processed_rows` and `batch.error_count` every N rows.
- Use a `with openpyxl.load_workbook(...) as wb:` context (B14).
- Optional: prefetch unique `area`/`location` names with one
  `bulk_create(..., ignore_conflicts=True)` pass before the row loop
  (B9).

### Step 5 — Admin progress UI

- Update `CompanyImportBatchAdmin.list_display` to include
  `step`, `progress_pct`, `error_count`.
- Add a `progress_pct` method on the model:
  `100 * processed_rows / total_rows` (guarded for `total_rows == 0`).
- Add a download link to the source file in the change view.
- (Optional) auto-refresh the change-list page every 5 s when any
  batch is in a non-terminal step.

### Step 6 — Tests

- Add a regression test where one row raises `IntegrityError`
  mid-loop (e.g. by patching `Company.objects.update_or_create` to
  raise on row 2) and assert that rows 1, 3, 4 still committed and the
  batch is `COMPLETED` with one error in `error_log`.
- Add a test that asserts `total_rows` and `processed_rows` are
  populated correctly.
- Fix template / help_text doc inconsistency (B10) covered by snapshot
  test or template smoke test.

---

## Quick-fix priority order

If only a handful of fixes can ship now, do these first:

1. **B1** — per-row atomic + try/except. (Correctness; without this the
   whole feature is fragile.)
2. **B3** — fix `PrivateMediaStorage()` instantiation in the model so
   local dev / CI work.
3. **B4** — add `total_rows` / `processed_rows` / `step` columns and
   update them; expose in admin list.
4. **B2** — move S3 upload into a background task.
5. **B5** — stream the download into the tempfile.
6. **B6** — validate file in the form.
7. **B10** — fix template/help_text mismatch.
8. **B19** — add the missing test for mid-loop failure.

The rest can land as cleanup PRs.
