## Context
The upload-timeout fix (`fix-excel-import-timeout`, archived 2026-05-06) decoupled the request thread from the celery worker by writing the upload to a local-filesystem volume and dispatching processing. That solved the operator-visible "Error al subir el archivo" timeout.

The follow-on problem this proposal addresses: worker processing of large xlsx files takes minutes, and during those minutes the admin batch detail page shows `Procesando` with all counters at zero. Operators have no way to distinguish "still working" from "hung." The current importer (`apps/companies/importers.py`) wraps the entire row loop in `with transaction.atomic():` (line 47) and calls `update_or_create` per row (line 107); counters are local variables that don't materialize on the `CompanyImportBatch` row until the loop completes and the outer transaction commits.

The user-reported case that triggered this proposal: 55 MB xlsx, ~150k rows, ~7 minutes processing time, batch row stuck on `Procesando` for the full duration with `created_count = 0`. Celery worker log confirmed the task was *received* but never *succeeded* — i.e. the function was running, slowly, with all writes invisible to the admin connection because of PostgreSQL Read Committed isolation.

Stakeholders:
- **Operators** running imports — need a live signal that work is progressing and how much is left.
- **Backend developers** — own the importer hot loop and the celery task lifecycle.
- **Admin / template maintainers** — own the change-form template override and the small JS poller.

## Goals / Non-Goals

**Goals**
- Operator MUST see `processed_rows / total_rows` and the three counter fields update without manual refresh while the import is running.
- Total processing time for a 150k-row file MUST drop from ~7 min to under 60 s.
- Existing test scenarios for `Enhanced Spanish XLSX Importer` (lowercase / ACTIVIDAD splitting / blacklist counting) MUST continue to pass with no behavior changes.
- Re-running a partially-imported file MUST converge to the same final state without creating duplicate `Company` rows.
- The proposal MUST NOT regress any of the 58 tests landed by `fix-excel-import-timeout`.

**Non-Goals**
- We will NOT introduce WebSockets, Server-Sent Events, or Django Channels. Polling at 2 s satisfies "real-time" for an internal admin workflow.
- We will NOT add per-user push notifications, Slack alerts, or completion emails. Out of scope.
- We will NOT swap openpyxl for another xlsx library. `read_only=True` streams rows efficiently enough.
- We will NOT introduce a separate "in-flight rows" or "import_chunk" table. The two new counter columns on `CompanyImportBatch` are sufficient.
- We will NOT introduce HTMX, Alpine, or any client-side framework. ~30 lines of vanilla JS is enough.

## Decisions

### Decision 1: Per-chunk transactions, not one big transaction
- **What**: Replace the importer's outer `with transaction.atomic():` with one `transaction.atomic()` per chunk of `COMPANY_IMPORT_CHUNK_SIZE` rows (default 1000). Each chunk's commit immediately exposes the new rows AND the updated counter values to other DB connections — notably the admin polling endpoint, which runs on a separate connection from the celery worker.
- **Why**: PostgreSQL's default Read Committed isolation means uncommitted writes are invisible to other connections. With a single 7-minute transaction, the admin always sees counters of zero until the moment the import finishes. Per-chunk commits are the simplest mechanism that makes counters visible to the admin in flight.
- **Trade-off**: Mid-import failures leave partial state. Mitigated by importer idempotency (`Company.email` is unique; existing rows go through bulk-update, new rows through bulk-create with `ignore_conflicts=True`) — re-running the same file converges to the same final state.
- **Alternatives considered**:
  1. **Single transaction with periodic `batch.save()` calls** — does not work; the saves are inside the same uncommitted transaction and are not visible to the admin connection.
  2. **`SAVEPOINT` + manual flush** — gives no visibility benefit (savepoints are still inside the outer transaction).
  3. **Async progress writes to Redis** — adds infra and a second source of truth; rejected.

### Decision 2: Bulk-create + bulk-update per chunk
- **What**: Inside each chunk, partition rows into "new email" and "existing email" buckets via a single `Company.objects.filter(email__in=[…]).values_list("email", "id")` lookup. Then `Company.objects.bulk_create([…], ignore_conflicts=True)` for new rows and `Company.objects.bulk_update([…], fields=[<all writable fields>])` for existing ones. Same pattern for `Area` and `Location` taxonomies — one `bulk_create(ignore_conflicts=True)` per taxonomy per chunk for new names.
- **Why**: Per-row `update_or_create` is the dominant cost in the current 7-minute import (each row = 4 SQL roundtrips: 1 SELECT for company, 1 INSERT/UPDATE for company, 2 for taxonomy resolution after cache miss). A 1000-row chunk drops from ~4000 SQL roundtrips to ~3. Total import time on a 150k-row file should drop from ~7 minutes to ~30–60 seconds.
- **Trade-off**: More complex partition / merge logic. Mitigated by tests for both buckets (one row already exists by email, one row is new, mix of both, all-new, all-existing).
- **Implementation note**: Django 4.1+'s `bulk_create(update_conflicts=True, update_fields=[...], unique_fields=["email"])` is a single-query alternative to the partition-and-bulk-update dance — worth using if the test matrix is shorter. Will evaluate at implementation time; either approach satisfies the spec.

### Decision 3: Polling, not push, for the dashboard
- **What**: Admin change-form template loads ~30 lines of inline JS that polls `/admin/companies/companyimportbatch/<id>/progress/` every 2 000 ms while `status in {PENDING, PROCESSING}`. On terminal status (`COMPLETED` / `FAILED`), polling stops and the page reloads once so the standard admin renders the final state (file field, error_log, status flag).
- **Why**: Polling at 2 s for a single-operator admin workflow is trivial load. Each request is a single primary-key lookup; with Django session middleware, admin auth, and a Postgres roundtrip, end-to-end latency lands in the ~10–30 ms range. At 30 req/min × ≤10 simultaneous watchers, this is well under 1 % of one CPU. SSE / WebSockets require either Channels (new infra: ASGI server, Redis pub-sub) or async views (architectural change to a sync codebase) — not justified at this load.
- **Cost ceiling**: an import that takes 60 s under the new bulk path produces ~30 polls. A cancelled import (operator closes the tab) stops polling immediately on the client side; the worker keeps processing.
- **Alternatives considered**:
  1. **Server-Sent Events** — pushy, single connection per watcher, but Django sync view + nginx default buffering (`proxy_buffering on`) make this fiddly without infra-side configuration. Rejected for v1.
  2. **Django Channels / WebSocket** — new deployment surface (Daphne, ASGI, Redis pub-sub). Rejected for v1.
  3. **HTMX `hx-trigger="every 2s"`** — clean ergonomics, but the project doesn't use HTMX; introducing it for one widget is over-investment.

### Decision 4: Preflight row count via `ws.max_row`
- **What**: Before chunk processing starts, `process_company_import` opens the workbook in `read_only=True`, reads `ws.max_row`, subtracts 1 for the header, clamps to `min(value, 5_000_000)`, writes it to `batch.total_rows`, and closes the workbook. The importer then reopens the workbook to iterate rows.
- **Why**: Operators want a denominator so the dashboard can render "12 345 / 150 000 (8.2%)". Without it, only an absolute count ticks up which doesn't communicate completion.
- **Trade-off**: `ws.max_row` can be inflated by phantom formatting (Excel sometimes thinks `max_row = 1 048 576` due to stray whole-column formatting). The `5_000_000` clamp is a defensive ceiling — if a file legitimately has more rows than that, the cap on `COMPANY_IMPORT_MAX_FILE_MB` (25 MB default) would have rejected it anyway.
- **Subtle cost**: opening + closing the workbook twice (preflight + iteration) adds ~hundreds of ms for a 55 MB file; acceptable.
- **Alternatives considered**:
  1. **Count rows during the iteration and surface them only at the end** — rejected; defeats the whole purpose since the operator can't see a percentage until completion.
  2. **Pass the loaded workbook handle from the celery task into the importer** — would save the second parse (~hundreds of ms). Rejected for v1: changes the importer's public signature, complicates the `batch=None` backward-compat path, and the savings are dwarfed by the chunked-bulk speedup. Worth revisiting if profiling shows preflight dominates.
  3. **Read row count from a cheap header-only stream parse (e.g. iter + drop)** — same cost as a full read-only open in practice; openpyxl's `read_only` is already streaming.

### Decision 5: Chunk size as a setting, default 1000
- **What**: `COMPANY_IMPORT_CHUNK_SIZE = config("COMPANY_IMPORT_CHUNK_SIZE", default=1000, cast=int)` in `config/settings.py`.
- **Why**: 1000 rows per chunk balances commit overhead (small enough to feel responsive: ~150 chunks for a 150k-row file, polling at 2 s sees ~5 chunks per poll) against per-chunk efficiency (large enough that bulk-write per-batch overhead is amortized).
- **Trade-off**: Smaller chunks (e.g. 100) over-commit and slow the importer. Larger chunks (e.g. 10 000) lose progress granularity. 1000 is a defensible default; tunable per deployment via the env var.

### Decision 6: Move `bust_filter_caches()` into the celery task
- **What**: Currently `import_companies_from_xlsx` calls `transaction.on_commit(bust_filter_caches)` after its single big commit. Move that call into `process_company_import` (after the importer returns successfully).
- **Why**: With per-chunk commits, leaving the call inside the importer would either over-bust (once per chunk = 150 times) or be silently dropped (because `transaction.on_commit` only fires once per outermost atomic block). Moving it to the task makes the cache-bust an unambiguous "import succeeded → invalidate" signal that fires exactly once.
- **Trade-off**: Operators viewing the public landing page during an in-flight import will see slightly stale taxonomy data until completion. Acceptable — public landing data is currently cached for 5 min anyway.

## Risks / Trade-offs

- **Risk**: Worker killed mid-chunk leaves a `PROCESSING` row with partial `processed_rows` and partial `created_count`. The dashboard polling shows the last committed values forever and never transitions to terminal status.
  **Mitigation**: This is the same shape as the orphan-`PENDING` problem from the upload-timeout proposal. Same answer: the periodic `purge_stale_company_import_files` sweep already handles file cleanup; a small extension to flip lingering `PROCESSING` rows older than ~30 min to `FAILED` (with explanatory `error_log`) is a clean follow-up. Not blocking for this proposal but tracked as Open Question 1.
- **Risk**: A retry from the operator on a partially-imported failed batch double-imports rows.
  **Mitigation**: `bulk_create(ignore_conflicts=True)` on the unique `Company.email` constraint silently skips already-imported rows. The bulk-update path catches the rest. Re-runs are idempotent.
- **Risk**: `bust_filter_caches` was relied upon by tests of `Cache and Invalidation for Filter Data`. Moving the call to the task changes the call site but not the user-visible invalidation moment.
  **Mitigation**: The existing scenario "Bulk import busts the cache exactly once" still holds — once per import, just from the celery task instead of the importer.
- **Risk**: The polling endpoint is a tight loop on the database. Even small queries × 30 polls/min × N watchers can chew connections.
  **Mitigation**: `progress_json` is a single `CompanyImportBatch.objects.only(...).get(id=...)` — one indexed primary-key lookup. Connection pooling (`conn_max_age=600` in `config/settings.py:81`) keeps it cheap.
- **Trade-off**: The mid-failure-leaves-partial-rows behavior is a real semantic change relative to the current all-or-nothing transaction. Documented in `Chunked Import Progress Tracking` so reviewers approve it explicitly.

## Migration Plan
1. Pre-deploy: confirm `purge_stale_company_import_files` is healthy (already verified by the upload-timeout proposal).
2. Apply migration `0011_companyimportbatch_progress`. Adds two `PositiveIntegerField` columns with `default=0` — Postgres adds these as a metadata-only operation (no table rewrite on Postgres 11+), so deploy is fast and non-blocking.
3. Deploy code change. New imports immediately get chunked behavior. Existing `COMPLETED` / `FAILED` rows are unaffected (their `total_rows` / `processed_rows` stay at 0; the change-form template gracefully renders without the progress widget for terminal-status batches).
4. Rollback: revert code commit. The two new fields stay in the DB (idempotent); old code ignores them. Caveat: any imports started under new code but still in `PROCESSING` will have their per-chunk-committed rows persisted; rollback does not retroactively roll those back. Expected and acceptable.

## Open Questions
1. Should we extend `purge_stale_company_import_files` (or add a sibling) to flip stale `PROCESSING` rows older than e.g. 30 min to `FAILED`? Recommend yes, but defer to a small follow-up proposal so this change stays scoped.
2. Should the change-form widget also show a sparkline / per-chunk timing graph? Out of scope for v1; reconsider if operators ask for it.
3. Should `total_rows` exclude blank rows (rows where every cell is empty) so the percentage doesn't lie when the file has trailing blanks? Probably yes — a small "skip blank rows" preflight pass would tighten the denominator. Tracked in tasks.
