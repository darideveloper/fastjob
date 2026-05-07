# Tasks: Chunked import with live progress

## 1. Settings and model
- [x] 1.1 Add `COMPANY_IMPORT_CHUNK_SIZE = config("COMPANY_IMPORT_CHUNK_SIZE", default=1000, cast=int)` to `config/settings.py` adjacent to the other `COMPANY_IMPORT_*` settings.
- [x] 1.2 Add two fields to `CompanyImportBatch` in `apps/companies/models.py`:
  - `total_rows = models.PositiveIntegerField(default=0)`
  - `processed_rows = models.PositiveIntegerField(default=0)`
- [x] 1.3 Run `python manage.py makemigrations companies`. Commit the result as `0011_companyimportbatch_progress.py`. Confirm the migration only contains `AddField` operations with `default=0` so Postgres applies it as a metadata-only change.
- [x] 1.4 In `apps/companies/admin.py`, extend `CompanyImportBatchAdmin.list_display` to include `total_rows` and `processed_rows`, and extend `readonly_fields` so they show on the change form.

## 2. Importer rewrite (chunked + bulk)
- [x] 2.1 In `apps/companies/importers.py`, change the function signature to `import_companies_from_xlsx(file_path, batch=None, chunk_size=1000)`. Default `batch=None` preserves the current call sites; default `chunk_size=1000` matches `COMPANY_IMPORT_CHUNK_SIZE`.
- [x] 2.2 Refactor the body so the row iterator accumulates rows into a chunk buffer. When the buffer reaches `chunk_size` (or the iterator exhausts), the chunk is processed in one `with transaction.atomic():` block and the buffer is cleared. Skip rows where every cell is empty BEFORE the row counter advances, so trailing blank rows do not inflate `processed_rows`.
- [x] 2.3 Inside the per-chunk block:
  - **Pre-validate every row BEFORE building the partition**: check email format (non-empty, contains `@`), check `name` non-empty, truncate strings to their `max_length`, and **manually lowercase** `email`, `name`, `address`, `province`, `community`, `website` (preserve the existing pattern at `apps/companies/importers.py:56-67`). Bad rows are appended to the cumulative `errors` list and are excluded from BOTH the bulk_create and bulk_update buckets — they MUST NOT reach the database. `ignore_conflicts=True` only suppresses unique-key conflicts, NOT generic integrity errors (NOT NULL, CHECK, etc.), so a malformed row hitting `bulk_create` would roll back the entire chunk.
  - **Critical**: `LowercaseFieldsMixin.save()` is bypassed by `bulk_create` and `bulk_update`, so the importer is the ONLY place that lowercases fields on the import path. The manual lowercasing is load-bearing — do not remove it under the assumption that the mixin "handles it."
  - Resolve / create `Area` and `Location` taxonomy rows in bulk: collect distinct (already-lowercased) names from the chunk, query existing rows once via `filter(name__in=[...])`, `bulk_create(ignore_conflicts=True)` for any still missing, then refresh the local cache. (`Area` / `Location` also use `LowercaseFieldsMixin` — same bypass concern; lowercase the names explicitly before the bulk path.)
  - Single lookup `Company.objects.filter(email__in=chunk_emails).values_list("email", "id")` builds the partition.
  - `bulk_create([Company(...), ...], ignore_conflicts=True)` for new rows (preserves email uniqueness invariant).
  - `bulk_update([Company(...), ...], fields=[<name, area, location, address, zip_code, province, community, phone, fax, website>])` for existing rows. (Do NOT include `email` or `created_at`: `email` is the row identity and `created_at` is `auto_now_add`.)
- [x] 2.4 After each chunk commit, if `batch is not None`, call an internal helper `_write_progress(batch, processed_rows, created, updated, blacklisted_skipped, errors)` that does `batch.save(update_fields=["processed_rows", "created_count", "updated_count", "blacklisted_skipped", "error_log", "updated_at"])`. Use the cumulative running totals, not chunk-local deltas.
- [x] 2.5 Remove the `transaction.on_commit(bust_filter_caches)` call from the importer (moved to the celery task per task 3.4 below).
- [x] 2.6 Preserve the public return tuple `(created, updated, errors, blacklisted_skipped)` so tests in `apps/companies/tests/test_importers.py` keep passing without modification.

## 3. Celery task integration
- [x] 3.1 In `apps/companies/tasks.py:process_company_import`, between the `PROCESSING` save and the importer call, add a preflight step (see **section 8** for the unreliable-`max_row` fallback that this step delegates to):
  - Open the workbook via `openpyxl.load_workbook(batch.file.path, read_only=True, data_only=True)`.
  - Read `ws.max_row` from the active sheet. Handle `None`, `0`, and `1` as "unreliable" and route to the streaming fallback per section 8.
  - Subtract 1 for the header row. Negative or zero results stay at `0`.
  - Clamp the upper end via `min(value, 5_000_000)` (defensive ceiling against phantom whole-column formatting that reports `max_row = 1_048_576`).
  - Save `batch.total_rows = clamped` via `batch.save(update_fields=["total_rows", "updated_at"])`.
  - Close the workbook before the importer reopens it. (See design.md §"Decision 4" for an alternative considered: passing the loaded workbook handle into the importer to avoid a second parse pass; deferred for v1.)
- [x] 3.2 Pass `batch=batch` and `chunk_size=settings.COMPANY_IMPORT_CHUNK_SIZE` into the `import_companies_from_xlsx(...)` call.
- [x] 3.3 On success, after the importer returns and before the file delete:
  - **Reconcile the denominator**: write `batch.total_rows = batch.processed_rows` and save with `update_fields=["total_rows", "updated_at"]`. The preflight `ws.max_row` estimate is intentionally an upper bound (it counts trailing blank rows); reconciling at the end pins the dashboard percentage to exactly 100 % on `COMPLETED`. This is cheap and matches operator intuition that a finished import shows 100 %.
  - Call `from .queries import bust_filter_caches; transaction.on_commit(bust_filter_caches)` exactly once.
- [x] 3.4 On the failure path (`except Exception`), do NOT zero `processed_rows` — leave whatever the last committed chunk wrote. Append the system error and traceback to `error_log` as today.

## 4. Admin progress endpoint
- [x] 4.1 In `apps/companies/admin.py`, add `progress_json(self, request, object_id)` on `CompanyImportBatchAdmin`. It MUST:
  - Look up the batch with `CompanyImportBatch.objects.only("status", "total_rows", "processed_rows", "created_count", "updated_count", "blacklisted_skipped", "error_log").get(id=object_id)` (single indexed query).
  - Return `JsonResponse({"status", "total_rows", "processed_rows", "created_count", "updated_count", "blacklisted_skipped", "error_count": len(batch.error_log or [])})`.
  - Return `404` (`Http404`) if the batch does not exist.
- [x] 4.2 Override `get_urls()` on `CompanyImportBatchAdmin` to register the route. Follow the project convention of placing custom routes BEFORE `super().get_urls()` (matches the existing `CompanyAdmin.get_urls()` pattern at `apps/companies/admin.py:85-88`). The trailing path component (`progress/` vs `change/`) means there is no actual collision risk — the ordering is purely conventional:
  ```python
  custom = [path("<int:object_id>/progress/", self.admin_site.admin_view(self.progress_json), name="companies_companyimportbatch_progress")]
  return custom + super().get_urls()
  ```
- [x] 4.3 Verify in dev that hitting `/admin/companies/companyimportbatch/<id>/progress/` returns the expected payload and that anonymous access redirects to login.

## 5. Admin change-form template (live progress widget)
- [x] 5.1 Add `change_form_template = "admin/companies/companyimportbatch/change_form.html"` to `CompanyImportBatchAdmin`.
- [x] 5.2 Create `templates/admin/companies/companyimportbatch/change_form.html` extending `admin/change_form.html`. In the `{% block content %}` (or just before `{{ block.super }}`), render a small progress widget that includes:
  - A `<progress>` element bound to `processed_rows / total_rows` (when `total_rows > 0`).
  - `<p>` line "<processed_rows>/<total_rows> filas procesadas (<percent>%)".
  - Counter widgets: "Creadas: X", "Actualizadas: Y", "En lista negra: Z", "Errores: N".
  - The whole widget is wrapped in `<div id="import-progress" data-batch-id="{{ original.id }}" data-status="{{ original.status }}" hidden>` so it can be hidden from the JS based on status.
- [x] 5.3 Add an inline `<script>` (~30 lines, vanilla JS) that:
  - Reads `dataset.batchId` and `dataset.status` from `#import-progress`.
  - If `status in {COMPLETED, FAILED}`, leaves the widget hidden and does nothing.
  - Otherwise unhides the widget and starts a 2 000 ms polling loop.
  - Each tick calls `fetch("/admin/companies/companyimportbatch/" + batchId + "/progress/")` and updates the DOM.
  - On a terminal status response, stops polling and calls `window.location.reload()` once so the standard admin renders the final state.
  - Uses `setTimeout`-based scheduling (not `setInterval`) to avoid stacking calls if the network is slow.
- [x] 5.4 Confirm the widget is invisible (no flash) for `COMPLETED` / `FAILED` batches on initial page render.

## 6. Tests
- [x] 6.1 Extend `apps/companies/tests/test_importers.py` to cover:
  - Chunked import with `chunk_size=2` produces correct totals across 5 rows (totals match: 5 created, 0 updated).
  - When a `batch` argument is passed, `processed_rows` is written after every chunk (assert via mocking `_write_progress` or by reading `batch.processed_rows` between chunks via a hand-built generator harness).
  - Re-running the same file on top of an existing partial import does not create duplicates and produces the same final `created_count` + `updated_count` totals. **Injection mechanism**: use `mock.patch` to wrap the inner per-chunk write helper so it raises on a specific chunk index (e.g. chunk 3 of 5), invoke the importer once and observe partial state, then re-run on the same file with the patch removed and assert the final state matches a clean run from scratch.
  - A row with an invalid email does not abort its chunk; the rest of the chunk is committed and the error appears in `errors`.
  - Trailing blank rows do NOT inflate `processed_rows`.
- [x] 6.2 Extend `apps/companies/tests/test_tasks.py` to cover:
  - `process_company_import` writes `total_rows` after preflight (assert `batch.total_rows > 0` after `process_company_import` runs on a 5-row file).
  - On success, `processed_rows == total_rows`.
  - `bust_filter_caches` is called exactly once on success (mock the function, run `process_company_import`, assert call count is 1).
  - The existing 58 tests still pass without modification.
- [x] 6.3 Add `apps/companies/tests/test_admin_progress.py` covering:
  - The progress endpoint returns the expected JSON shape and values for a `PROCESSING` batch (assert keys, assert types, assert `error_count == len(error_log)`).
  - Anonymous access returns a 302 redirect to the admin login page.
  - `progress_json` returns 404 for a nonexistent batch.
  - The change-form HTML for a `PROCESSING` batch contains `id="import-progress"` and `data-status="PROCESSING"`.
  - The change-form HTML for a `COMPLETED` batch contains `data-status="COMPLETED"` (and the JS will leave the widget hidden).
- [x] 6.4 Use `tmp_path` + `override_settings(COMPANY_IMPORT_LOCAL_PATH=str(tmp_path), COMPANY_IMPORT_CHUNK_SIZE=2)` in any test that exercises chunking, to keep tests deterministic and isolated.

## 7. Diagnostic upload-view error path
Discovered post-implementation: when migration `0011_companyimportbatch_progress` was not yet applied to the local database, `CompanyImportBatch.objects.create(status="PENDING")` at `apps/companies/admin.py:107` raised `django.db.utils.ProgrammingError: column "total_rows" does not exist`. The wrapping `except (OSError, SuspiciousFileOperation)` clause at line 111 did NOT catch it, so Django returned an unhandled 500. The upload XHR in `templates/admin/companies/import_xlsx.html` then fell back to the generic Spanish string "Error al subir el archivo. Por favor inténtalo de nuevo.", giving the operator no clue *why* the upload failed. This section makes that error path diagnostic.

- [x] 7.1 In `apps/companies/admin.py:import_xlsx_view`, broaden the exception handler that currently catches `(OSError, SuspiciousFileOperation)` so it also catches `Exception` as a final arm (kept narrow first, generic last). The generic arm MUST:
  - Log the full traceback via `logger.exception("import_xlsx_view: unhandled error during batch creation")`.
  - For XHR requests, return `JsonResponse({"error": f"Error inesperado: {type(exc).__name__}: {exc}"}, status=500)` — naming the exception class so operators can distinguish a `ProgrammingError` (schema drift) from an `OperationalError` (DB down) from anything else without opening server logs.
  - For non-XHR requests, surface `messages.error(request, ...)` with the same diagnostic message and redirect to `..`.
  - If a `CompanyImportBatch` row was already created before the failure, mark it `FAILED` with the exception details on `error_log` so the audit trail in `/admin/companies/companyimportbatch/` stays consistent with the spec's "exactly one batch per upload attempt" guarantee.
- [x] 7.2 In `apps/companies/admin.py`, move the `Http404` import out of `progress_json` and up to the module-level Django imports next to `JsonResponse`, for consistency with the rest of the file.
- [x] 7.3 Add a test in `apps/companies/tests/test_admin_import_view.py` that:
  - Patches `CompanyImportBatch.objects.create` to raise `django.db.utils.ProgrammingError("column 'total_rows' does not exist")`.
  - POSTs an XHR upload to the import view and asserts the response is a 500 with a JSON body whose `error` field contains the substring `"ProgrammingError"` AND the original error message.
  - Asserts the generic fallback string from the upload XHR is NOT what surfaces — the diagnostic message is.

## 8. Preflight robustness for unreliable `ws.max_row`
Discovered post-implementation: the user uploaded a real xlsx file and saw `Total rows = 0` in the admin throughout processing. Root cause: the producing tool either omitted the worksheet `<dimension>` element (so `ws.max_row` returned `None`) or emitted a placeholder `<dimension ref="A1:B1"/>` (so `ws.max_row` returned `1`). The original preflight collapsed both to `total_rows = 0` via `max((None or 0) - 1, 0) = 0`, leaving the live progress widget without a denominator. Naively falling through to `iter_rows` did NOT fix the placeholder case because openpyxl's `iter_rows` honors `self.max_row` as an upper bound and stops at row 1.

- [x] 8.1 Update `_preflight_total_rows` in `apps/companies/tasks.py` so it:
  - Reads `ws.max_row` first (cheap path; near-zero cost for well-formed Excel files).
  - When `ws.max_row` is `None`, `0`, or `1`, calls `ws.reset_dimensions()` to clear openpyxl's internal `_max_row` cap (the documented openpyxl escape hatch — its docstring even says "this probably indicates a bug in the library or application that created the workbook").
  - Stream-counts the rows via `sum(1 for _ in ws.iter_rows(values_only=True))`. In `read_only=True` mode this is a lazy XML walk with bounded memory; ~1-2s for 150k rows, dwarfed by the import itself.
  - Continues to clamp to `_MAX_ROWS_CLAMP = 5_000_000` defensively.
- [x] 8.2 Update the docstring on `_preflight_total_rows` to explain the fast-path / slow-path split and why `reset_dimensions()` is required before the fallback `iter_rows` (otherwise the placeholder bound makes the fallback also yield 0).
- [x] 8.3 Add a regression test `test_preflight_falls_back_to_streaming_when_max_row_is_unreliable` to `apps/companies/tests/test_tasks.py`. Faithful simulation: patch `ReadOnlyWorksheet.__init__` to overwrite `self._max_row` post-init (which is exactly the state a non-conformant producer creates — patching the class-level property does NOT simulate this faithfully because `reset_dimensions()` operates on the instance attribute, not the property). Cover both real-world failure modes:
  - Case 1: producer omitted `<dimension>` entirely → `_max_row = None`.
  - Case 2: producer wrote a placeholder dimension → `_max_row = 1`.
  - In both cases the preflight MUST return `5` for a real 5-row file (+ header).

## 9. Validation and rollout
- [x] 9.1 Run `openspec validate add-chunked-import-progress --strict` and resolve any reported issues.
- [x] 9.2 Run `pytest apps/companies/tests/` locally; expect ≥ 71 passed (the 58 prior + ≥ 13 new — chunking, admin progress, diagnostic upload, preflight fallback).
- [x] 9.3 **Apply migration locally before any manual verification.** Run `python manage.py migrate companies` and confirm via `python manage.py showmigrations companies | tail -5` that `0011_companyimportbatch_progress` shows `[X]`. This step is non-optional: skipping it reproduces the upload error that motivated section 7.
- [ ] 9.4 Manually verify with the 55 MB / ~150 k-row xlsx that triggered this proposal:
  - Total processing time drops to under 60 s.
  - Progress bar advances visibly and smoothly during the import.
  - **`Total rows` is non-zero on the first poll** (validates the section 8 fix end-to-end against a real producer).
  - Final counters match expectations.
  - Re-running the same file is idempotent (no duplicate `Company` rows).
- [ ] 9.5 Apply migration in production / deploy code change. Confirm `/healthz` still passes. Verify that `python manage.py showmigrations companies` on the production target shows `0011` applied before declaring rollout done.
- [ ] 9.6 After 7 days in production, archive with `openspec archive add-chunked-import-progress`.
