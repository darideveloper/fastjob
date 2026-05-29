# FastJob — Development Log

A running record of what's been built, what's in progress, and what's pending.
Newest entries at the top.

---

## 2026-05-28 — Session 6: Relink redirect loop & unlinking removal

### Done

- **Fixed Relink Redirect Loop:** Modified "Vincular ahora" in the dashboard warning banner to point to `/accounts/logout/` (via `account_logout` url name) instead of `/accounts/login/` to resolve the redirection loop.
- **Removed Account Unlinking:** Unmounted `/accounts/3rdparty/` routes and deleted the unused `templates/socialaccount/connections.html` template to completely disable manual user unlinking of social accounts.
- **Added Defensive Safeguard:** Registered a defensive dummy redirect named `socialaccount_signup` pointing to `/accounts/login/` in `config/urls.py` to prevent potential NoReverseMatch errors in `django-allauth`.
- **Aligned Test Suite:**
  - Replaced connections url preservation test with assertions verifying `/accounts/3rdparty/` is unmounted (Resolver404) and `socialaccount_signup` redirects safely.
  - Aligned pause notification tests in `test_pause_notifications.py` and `test_repro_notification.py` to match the newly unified branded email subjects and bodies.
  - Fixed `test_storage.py` to use a hermetic mock-boto3 storage approach, bypassing the static test settings overrides.

### Validation

- All 386 tests successfully pass under virtualenv.

---

## 2026-04-24 — Session 5: P1 tail + full P2 sweep

### Done

- **Flower sidecar wired** (last P1 item) — added `flower` service to `docker-compose.yml` bound to `127.0.0.1:5555` only, HTTP Basic auth from `FLOWER_BASIC_AUTH` env var (`.env.example` shipped with `admin:changeme` placeholder + warning). `flower==2.0.1` added to `requirements.txt`. Nginx reverse-proxy snippet documented in `deploy.md`.
- **Multi-CV support** (biggest P2) — introduced `CV` model (`apps/accounts/models.py`) with `user`, `file`, `name`, `created_at`. Replaced `User.cv_file` + `User.cv_updated_at` with a single `User.active_cv` FK. Added `MailingLog.cv` FK so downloads serve the snapshot at send-time, not the currently-active CV. Dashboard now lists all CVs with "Usar" / "Eliminar" actions. Delete of the active CV falls back to the newest remaining CV, or clears + pauses the campaign if none remain. `CV.delete()` overridden to remove the Spaces object alongside the DB row.
- **Atomic CV replacement** (subsumed by multi-CV) — old behavior deleted the existing file before saving the new one; a mid-upload failure left users with no CV. New `upload_cv` creates a new `CV` row, leaves the old one alone, and just re-points `active_cv`. The old CV stays accessible to the user until they explicitly delete it.
- **Dashboard pagination** — `recent_logs` now paginated via Django's `Paginator`, 20 per page, `?page=N` in URL. Template shows page X of Y + prev/next buttons.
- **Dashboard analytics** — new stat cards: **Enviados hoy**, **últimos 7 días**, **CVs enviados** (cumulative), **fallidos**. All server-side aggregates over `MailingLog` — no tracking pixels, no external services, so recipient deliverability is unaffected.
- **Admin email template preview** — new URL `/admin/mailing/emailtemplate/<id>/preview/` renders the template with sample placeholder values in a recipient-style frame. Surfaces `KeyError` for unknown placeholders as a visible red warning (catches typos before activating).
- **GDPR deletion flow** — two paths:
  - **User-initiated:** `/dashboard/eliminar-cuenta/`, requires typing own email verbatim to confirm. Deletes CVs from Spaces, then user row (cascades `MailingLog`, `SocialAccount`, `SocialToken`). `StripePayment.user` uses `SET_NULL` so payment audit trail survives anonymously.
  - **Admin-initiated:** `python manage.py delete_user --email X --yes` management command. Same deletion semantics; useful for support requests / scripted compliance.
- **Stripe customer ID caching** — added `User.stripe_customer_id` (indexed, blank-defaulted). Webhook handler back-fills it from `session["customer"]` on `checkout.session.completed`. `billing_portal` view prefers the cached ID; only falls back to `stripe.Customer.list(email=...)` when empty, and caches the result. Eliminates the extra API round-trip on every portal visit after first-pay.

### Schema changes

- `accounts/0002_cv_model_and_customer.py`: creates `CV`, adds `User.active_cv` FK + `User.stripe_customer_id` + data migration copying existing `cv_file` values, then drops `cv_file` / `cv_updated_at` columns.
- `mailing/0003_mailinglog_cv.py`: adds `MailingLog.cv` FK (`SET_NULL` on delete).

### Tests (63 total, all pass; 19 new)

- `apps/accounts/tests/test_cv_model.py` (5) — multi-CV, `has_cv` logic, cascade on user delete, `SET_NULL` on active CV delete.
- `apps/accounts/tests/test_delete_user_command.py` (2) — command removes user + CVs; errors on unknown email.
- `apps/dashboard/tests/test_dashboard.py` (8) — pagination, analytics counts (today/week/failed), upload creates new row, set-active switches pointer, delete-active falls back, delete-last pauses campaign, self-deletion guards on email match.
- `apps/mailing/tests/test_admin_preview.py` (3) — preview renders with placeholders, surfaces template errors, non-staff blocked.
- `apps/payments/tests/test_billing_portal.py` (+1 new test): cached `stripe_customer_id` skips the email lookup; webhook back-fills the ID on first successful payment.

### Validation

- `pytest -q` → **63 passed in ~2.5s**.
- `manage.py check --settings=config.test_settings` → 0 issues.
- `manage.py makemigrations --check --dry-run` → No changes detected.

### Docs updated

- `docs/features/cv-management.md` — rewrote the opening + tech-specs tables for multi-CV, documented `MailingLog.cv` snapshot behavior, new upload semantics.
- `docs/features/user-dashboard.md` — documented new views (`set_active_cv`, `delete_cv`, `delete_account`) and the new analytics + pagination context keys.
- `docs/features/email-templates.md` — new "Live preview in admin" subsection.
- `docs/features/payments.md` — updated Customer Portal section to reflect cached-ID behavior + webhook back-fill.
- `docs/features/admin-panel.md` — added "GDPR deletion (CLI)" section with both flows.
- `docs/deploy.md` — rewrote the Flower subsection now that it's a real default service (previously was just a YAML snippet to copy).

### Design notes

- **Why `CV` lives in `apps/accounts`, not its own app:** the model is 100% user-owned data, with no lifecycle independent of the User. Splitting into a dedicated `cvs` app would add an import edge and migrations dependency for no conceptual gain. Placing it next to `User` matches the "the user is the aggregate root" mental model.
- **Why `MailingLog.cv` and not just store the file path as a string:** with `ForeignKey + SET_NULL`, a deleted CV naturally produces a 404 on the download endpoint. If we'd stored a file path, the engine would try to generate a pre-signed URL for an object that no longer exists and the recipient would get a confusing S3 403 instead of a clean "not found" page.
- **Why user-initiated delete requires typing the email:** GDPR requires the user's deletion intent to be unambiguous. A single button click is too easy to misfire; typing the exact email is the standard "dangerous action" confirmation pattern. Same reason `rm -rf` won't accept `-f` alone on an interactive shell.
- **Why pagination at 20 per page:** matches the original hardcoded limit, so the default view is identical for users with < 20 logs (no sudden UX shift). Users with thousands of logs get a reasonable first-page payload + navigation.
- **Why Flower binds to `127.0.0.1` not `0.0.0.0`:** preventing the default-password Flower from being reachable from the internet. Operators must explicitly reverse-proxy it through Nginx (with stronger auth at that layer if needed) to make it accessible — a deliberate speed bump against accidental public exposure.
- **Why skip P3 items now:** log explicitly gates them. i18n is orthogonal to product-market fit for a Spanish-only market; Gunicorn tuning without traffic data would be guessing; ClamAV requires an ops daemon (clamd) and a threat model update. All three are fine to defer until a real trigger arrives.

### Pending (TODO) — by priority

#### P1 — Operational ✅ COMPLETE

#### P2 — Product quality ✅ COMPLETE

#### P3 — Defer unless triggered

- [ ] **i18n** — only if expanding beyond Spanish markets. Would require wrapping every template string in `{% trans %}` and `_()` in views — high churn, zero benefit today.
- [ ] **Gunicorn tuning** — wait for real traffic numbers. Current `--workers 3` is a reasonable default for 1-2 vCPU servers.
- [ ] **ClamAV scanning** of uploaded CVs — trust model currently assumes benign uploads. Triggers: admin-reported malicious PDF, or a platform (e.g. VirusTotal) flagging a hosted CV link.

---

## 2026-04-24 — Session 4: P1 Operational

### Done

- **Health check endpoint** — `GET /healthz` in `config/health.py`. Pings PostgreSQL (`SELECT 1`) + Redis cache (`set/get` round-trip). Returns 200 with `{"status":"ok","db":true,"cache":true}` when both pass, 503 with the failing component flipped to `false` otherwise. Exposed publicly (no auth) for external uptime monitors.
- **CI pipeline** — `.github/workflows/ci.yml` runs on push/PR to `main`. Steps: `manage.py check`, `makemigrations --check --dry-run`, `pytest -q`. Uses `DJANGO_SETTINGS_MODULE=config.test_settings` so no GitHub secrets / external services needed.
- **`social_account_removed` handler** — `apps/accounts/signals.py` auto-pauses the user's campaign when they unlink their OAuth account. Avoids the engine churning through `FAILED` logs on every tick after a disconnect.
- **Stripe Customer Portal** — `POST /payments/portal/` (view `billing_portal`). Gated on ≥1 completed `StripePayment`. Looks up the Stripe customer by email (`stripe.Customer.list(email=...)`) — no local `customer_id` column, trading one extra API call for avoiding a migration. Link surfaced on dashboard under the credits card as "Facturación".
- **DB backup script** — `scripts/backup_db.sh` — `pg_dump | gzip` → S3-compatible Spaces upload. Env-driven (DB + AWS creds + `BACKUP_BUCKET`). Designed for nightly cron: `0 3 * * * root /opt/fastjob/scripts/backup_db.sh >> /var/log/fastjob-backup.log 2>&1`. Retention handled at the bucket level via lifecycle policy (documented in `deploy.md`).
- **Celery monitoring** — documented Flower as a docker-compose sidecar in `deploy.md`; not wired into the default stack (keeps the production bundle lean, avoids exposing another port). Users who need queue visibility can opt in.

### Tests (44 total, all pass; 9 new)

- `apps/mailing/tests/test_health.py` (3) — happy path 200; DB down → 503; cache down → 503.
- `apps/accounts/tests/test_signals.py` (2) — unlink pauses active campaign; already-paused campaign is left alone.
- `apps/payments/tests/test_billing_portal.py` (4) — login required; blocks users with no completed payments; blocks when Stripe has no customer for the email; redirects to Stripe-hosted billing session URL on happy path.
- All 35 existing tests from sessions 1–3 continue to pass.

### Validation

- `pytest -q` → **44 passed in ~2s**.
- `manage.py check --settings=config.test_settings` → 0 issues.
- `manage.py makemigrations --check --dry-run --settings=config.test_settings` → No changes detected.

### Docs updated

- `docs/features/monitoring.md` — added `/healthz` section + CI subsection in the Testing block.
- `docs/features/payments.md` — added "Stripe Customer Portal" subsection.
- `docs/features/authentication.md` — added "Auto-pause on OAuth unlink" section describing the new signal.
- `docs/deploy.md` — added backup-script instructions (cron + env vars + lifecycle retention note), Flower sidecar example, CI subsection, and a `/healthz` verification step in the post-deploy checklist.

### Design notes

- **Why look up Stripe customer by email instead of storing `stripe_customer_id`:** avoids a schema migration for a low-traffic endpoint. The `stripe.Customer.list(email=...)` call adds ~100ms of latency per portal visit — acceptable for a feature users hit once per invoice. If traffic changes, switch to storing the ID on the User model and populating it in the webhook handler.
- **Why the `social_account_removed` handler only pauses, not deletes:** users often unlink by accident (clicking through consent screens), then re-link. Preserving campaign config (filters, credits, CV) means they just need to toggle the campaign back on after re-linking. Matches the re-link notification flow.
- **Why the backup script lives in `scripts/` not a management command:** pg_dump streams are cleanest from the shell; wrapping them in Django just adds a Python interpreter to the path. Also lets ops run the script via cron without loading the whole Django app.
- **Why CI uses `config.test_settings` for `manage.py check`:** base settings require `DB_PASSWORD` which has no default, so `check` would fail without it. `test_settings` pre-sets safe dummy values. A side benefit: CI is fully hermetic — no PostgreSQL container, no Redis, no secrets.

### Pending (TODO) — by priority

#### P1 — Operational (remaining) ✅ COMPLETED (Session 5, 2026-04-24)

- [x] **Celery monitoring via Flower** — docker-compose service wired in, 127.0.0.1-bound, HTTP Basic auth via `FLOWER_BASIC_AUTH`.

#### P2 — Product quality ✅ COMPLETED (Session 5, 2026-04-24)

- [x] **Admin email template preview** — live placeholder render at `/admin/mailing/emailtemplate/<id>/preview/`.
- [x] **GDPR deletion flow** — `delete_user` management command + `/dashboard/eliminar-cuenta/` self-service view.
- [x] **Dashboard analytics** — server-side aggregates (sent today/week/failed), no tracking pixels.
- [x] **Multi-CV support** — `CV` model + `User.active_cv` + `MailingLog.cv` snapshot.
- [x] **Store `stripe_customer_id` on User** — back-filled by webhook, cached by `billing_portal`.
- [x] **Dashboard pagination** for `recent_logs` — 20/page via Django `Paginator`.
- [x] **Atomic CV replacement** — subsumed by multi-CV (new row created before `active_cv` swap).

#### P3 — Defer unless triggered

- [ ] **i18n** — only if expanding beyond Spanish markets.
- [ ] **Gunicorn tuning** — wait for real traffic numbers.
- [ ] **ClamAV scanning** of uploaded CVs — trust model assumes benign uploads today.

---

## 2026-04-23 — Session 3: P0 Ship-stoppers

### Done
- **Logging:** structured `LOGGING` dict in `config/settings.py`. Per-module levels (mailing/payments at INFO, `django.db.backends` at WARNING to silence query noise). Console-only — suitable for Docker / PaaS log drains.
- **Sentry:** env-gated init in `settings.py` (no-op when `SENTRY_DSN` is empty). Wires `DjangoIntegration`, `CeleryIntegration`, and `LoggingIntegration(event_level=ERROR)`. `send_default_pii=False` because OAuth tokens + emails are sensitive.
- **Redis cache:** `django-redis` backend on db 1 (separate from Celery's db 0). `IGNORE_EXCEPTIONS=True` so a Redis blip doesn't 500 the site.
- **Rate limiting:** `@ratelimit(key='ip', rate='30/h')` on `cv_download`, `'10/h'` on `unsubscribe`. Custom `apps/mailing/middleware.py:RatelimitMiddleware` converts `Ratelimited` → HTTP 429 (default library behavior is 403, which misleads CDNs).
- **Production security headers:** all env-gated in `config/settings.py`. Includes CSP-adjacent (`X_FRAME_OPTIONS=DENY`, `SECURE_REFERRER_POLICY`, `SECURE_CONTENT_TYPE_NOSNIFF=True`), TLS (`SECURE_SSL_REDIRECT`, HSTS family, `SECURE_PROXY_SSL_HEADER`), and cookies (`SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `CSRF_TRUSTED_ORIGINS`).
- **Test infrastructure:** `pytest.ini`, `conftest.py` with reusable fixtures (`google_linked_user`, `microsoft_linked_user`, `company`, `email_template`), `config/test_settings.py` overriding DB → SQLite in-memory, Celery → eager, cache → locmem, storage → filesystem, password hasher → MD5 (dev speed).
- **Tests written (35 total, all pass):**
  - `apps/mailing/tests/test_engine.py` (8 tests) — OAuth token refresh (Google + Microsoft), Gmail send, Graph send, no-linked-account, API failure propagation.
  - `apps/mailing/tests/test_tasks.py` (9 tests) — happy path, slow-drip interval, blacklist, cooldown, area filter, token expiry → pause, no-credits, no-CV, no-templates.
  - `apps/mailing/tests/test_views.py` (7 tests) — unsubscribe + idempotency, unknown tokens → 404, CV download redirect, rate-limit 429.
  - `apps/payments/tests/test_webhook.py` (4 tests) — signature rejection, credit grant, idempotency on replay, unknown event types.
  - `apps/companies/tests/test_importers.py` (6 tests) — create/update, bad emails, missing headers, empty file, case-insensitive emails.

### Validation
- `pytest` → **35 passed in 2.18s**.
- `manage.py check` → 0 issues.
- `manage.py check --deploy` with production env vars → only W005 / W021 (HSTS subdomain + preload), intentionally left off by default (both are one-way doors).

### Design notes
- Why `pytest-django` over Django's `TestCase`: fixture composition is cleaner when you need "user → linked social account → token" stacked setups.
- Why not re-use DB between tests (`--reuse-db`): seed migrations are data (3 templates + 3 packages + SystemSettings row), and we need them present for realistic scenarios. In-memory SQLite migrates in ~200ms per test run, not worth the trouble.
- Why a dedicated `test_settings.py`: forces `CELERY_TASK_ALWAYS_EAGER=True` (tasks run synchronously, exceptions surface), and unconditionally disables Sentry so test runs don't pollute the error tracker.
- Why Ratelimit middleware: the library raises `Ratelimited` which Django's default handler 403s. 429 is the correct HTTP semantic and CDNs / Prometheus exporters know how to count it.

---

## 2026-04-23 — Session 2: Polish & Seed Data

### Done
- Created `log.md` (this file) to track progress going forward.
- Fixed dangling `{% for feature %}{% endfor %}` stub in `templates/home.html`.
- Generated initial Django migrations: `accounts/0001`, `companies/0001`, `mailing/0001`, `payments/0001`.
- Added custom allauth login template (`templates/account/login.html`) in Spanish, with Google + Microsoft buttons.
- Added data migration `apps/mailing/migrations/0002_seed_templates.py` with 3 sample email variants (Directo, Breve, Motivacional) + SystemSettings singleton row.
- Added data migration `apps/payments/migrations/0002_seed_packages.py` with Starter (9.99€ / 50) / Pro (29.99€ / 200) / Elite (69.99€ / 600).
- Added signal `apps/accounts/signals.py` granting 5 free credits on signup, wired via `AppConfig.ready()`.
- Added `README.md` with full setup (OAuth apps, Stripe, Spaces, Celery) and architecture diagram.
- Added `.gitignore`.

### Validation
- `manage.py check` → 0 issues.
- `manage.py makemigrations --check --dry-run` → "No changes detected" (models ↔ migrations aligned).
- Applied full migration stack against SQLite in-memory: 3 templates + 3 packages + SystemSettings(5 min, 12 hr) created successfully.

### Pending (TODO) — by priority

#### P0 — Ship-stoppers ✅ COMPLETED (Session 3, 2026-04-23)
- [x] **Logging + Sentry** — structured LOGGING dict with per-module levels; Sentry init env-gated on `SENTRY_DSN`. Celery + Django + logging integrations wired.
- [x] **Tests for mailing engine** (mocked Google/MS APIs) + Stripe webhook + importer — **35 tests, all passing in 2.2s**.
- [x] **Rate limiting** on `cv_download` (30/h/IP) and `unsubscribe` (10/h/IP). Redis cache backend + custom middleware to convert `Ratelimited` → HTTP 429.
- [x] **Production security** — all env-gated: `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD`, `SECURE_CONTENT_TYPE_NOSNIFF`, `SECURE_REFERRER_POLICY`, `X_FRAME_OPTIONS`, `CSRF_TRUSTED_ORIGINS`, `SECURE_PROXY_SSL_HEADER`.

#### P1 — Operational ✅ COMPLETED (Sessions 4–5)
- [x] **Health check endpoint** (`/healthz`) — DB + Redis ping. Implemented in `config/health.py`.
- [x] **CI pipeline** — GitHub Actions at `.github/workflows/ci.yml`.
- [x] **Celery monitoring** — Flower sidecar wired into `docker-compose.yml`, 127.0.0.1-bound, basic-auth env-var. Session 5.
- [x] **`social_account_removed` handler** — pauses campaign on OAuth unlink.
- [x] **Stripe Customer Portal** — `POST /payments/portal/`, linked from dashboard.
- [x] **DB backup strategy** — `scripts/backup_db.sh` + nightly cron documented.

#### P2 — Product quality ✅ COMPLETED (Session 5, 2026-04-24)
- [x] **Admin email template preview** — live placeholder render.
- [x] **GDPR deletion flow** — delete User + logs + CV file + OAuth tokens.
- [x] **Dashboard analytics** — server-side aggregates (no tracking pixels, deliverability preserved).
- [x] **Multi-CV support** — `CV` model + `User.active_cv` + `MailingLog.cv` snapshot FK.

#### P3 — Defer unless triggered
- [ ] **i18n** — only if expanding beyond Spanish markets.
- [ ] **Gunicorn tuning** — wait for real traffic numbers.

### Known limitations / design decisions
- **Tokens:** Google refresh tokens are only issued with `access_type=offline` + `prompt=consent` — already configured. Users who previously granted without `offline` won't get a refresh token and will hit re-link flow sooner.
- **Singleton `SystemSettings`:** enforced via `save(pk=1)` override. Admin "add" is hidden when one exists. Not using django-solo to avoid extra dependency.
- **`MailingLog.company_email_snapshot`:** we snapshot the email because `Company.on_delete=SET_NULL` — the log must remain readable even if the company is deleted later (GDPR/audit trail).
- **CV pre-signed URLs:** 5-minute TTL (`AWS_QUERYSTRING_EXPIRE = 300`). Shorter = safer (links can't be shared). Adjust in settings if users complain about expired links.

---

## 2026-04-23 — Session 1: Initial Build

### Done
- Project scaffold: `config/` (settings, urls, celery, wsgi), 5 apps under `apps/`.
- Custom `User` model extending `AbstractUser` (`credits_remaining`, `is_campaign_active`, `cv_file`, `area_filter`, `location_filter`).
- `Company` + `Blacklist` models; `.xlsx` importer with admin integration.
- `EmailTemplate`, `MailingLog`, `SystemSettings` (singleton) models.
- `CreditPackage` + `StripePayment` models.
- Mailing engine: `engine.py` with Gmail REST API + Microsoft Graph send, OAuth2 refresh flow.
- Celery task `process_mailing_queue`: slow-drip (5 min/user, 12 hr/company), random template pick, blacklist + cooldown filtering.
- Re-link notification task fired when OAuth token expires.
- Views: dashboard (CV upload, filters, campaign toggle), Stripe checkout + webhook, CV download (pre-signed S3 URL), unsubscribe.
- Templates: `base.html`, `home.html`, `dashboard/index.html`, `payments/packages.html`, `payments/success.html`, `mailing/unsubscribe.html`, `mailing/cv_not_found.html` — all Tailwind CDN, Spanish UI.
- Admin: custom User, Company (with Excel import action), Blacklist, EmailTemplate, MailingLog (read-only), SystemSettings (singleton), CreditPackage, StripePayment.
- `docker-compose.yml` with db / redis / web / celery_worker / celery_beat.
- Management command `setup_periodic_tasks` to register the Celery beat entry.
- `requirements.txt` with PyJWT + cryptography (both required by allauth's Google provider).

### Validation
- `python manage.py check` → "System check identified no issues (0 silenced)."
- All `.py` files parse cleanly (ast check).
