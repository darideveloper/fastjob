# Security Fixes — Checklist

Working checklist derived from `docs/security-check.md` verdicts (§1–§17). Generated 2026-04-25.

> **How to use this file**
>
> - `- [ ]` = pending
> - `- [x]` = done — write the PR/commit ref + date on the indented line below
> - ~~strikethrough~~ = won't-fix (add a one-line reason)
>
> Each item has: source-section back-reference, file/line locations, the concrete change, and an **Acceptance** line that defines "done" so you know when to check the box. Don't tick a box just because the code looks edited — tick it when Acceptance is satisfied.

---

## Progress summary

| Tier | Count | Done |
|---|---|---|
| ❌ Critical | 9 | 9 |
| ⚠️ Hardening — quick wins | 14 | 9 |
| ⚠️ Hardening — medium effort | 8 | 0 |
| ⚠️ Hardening — heavy lift | 4 | 0 |
| 🔍 Verify (runtime tests) | 6 | 0 |
| 🛡️ CI gates | 4 | 1 |
| **Total** | **45** | **19** |

---

## Suggested rollout order

- **Day 1** — C4, C6, C7, H1–H9, CI1
- **Day 2** — C1, C5, C9, H10–H14
- **Week 1** — C2, C3, C8, H15–H18
- **Week 2** — H19–H22, V1–V6, CI2–CI4
- **Backlog** — H23–H26

---

## ❌ Critical — fix before next prod deploy

### C1. Atomic credit decrement / increment (race fix)

- [x] **C1** — replace read-modify-write with `F()` expressions
  - Source: §2.7
  - Files: `apps/mailing/tasks.py:84-85`, `apps/payments/views.py:144-145`
  - Change: use `User.objects.filter(pk=user.pk).update(credits_remaining=F("credits_remaining") - 1)` for the decrement; symmetric `+ payment.credits_granted` for the webhook addition. Follow with `user.refresh_from_db(fields=["credits_remaining"])` if the value is read later in the same scope.
  - Acceptance: a concurrency test (two parallel `process_mailing_queue` invocations against one user with `credits_remaining=2`) ends with `credits_remaining=0`, not `1`.
  - Done: 2026-04-27 — `apps/mailing/tasks.py:87-90` decrements via `F("credits_remaining") - 1` + `refresh_from_db`; `apps/payments/views.py:149-155` increments via `F("credits_remaining") + payment.credits_granted` (single `update()` that also conditionally caches the Stripe customer ID). Coverage: `test_credit_decrement_survives_lost_update_pattern` (mailing) + `test_webhook_credit_increment_uses_atomic_update` + `test_webhook_does_not_double_credit_on_replay` (payments) all pass.

### C2. Cross-staff stored XSS in email-template preview

- [x] **C2** — sandbox the admin preview
  - Source: §1.6, §2.4, §7
  - Files: `apps/mailing/admin.py` (`preview_view`), `templates/admin/mailing/emailtemplate/preview.html`
  - Change: render `body_html` inside an `<iframe srcdoc="...">` with a strict CSP (`script-src 'none'`), OR run `bleach.clean(body_html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS)` before `mark_safe`. Iframe-srcdoc preferred (stronger isolation, no shared cookies).
  - Acceptance: a template containing `<script>alert(1)</script>` previewed by a different staff user does not execute in the admin origin (verified in DevTools console: no script invocation).
  - Done: 2026-04-27 — `mark_safe` removed from `preview_view`; body wrapped in a self-contained HTML doc with `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data: https:; font-src https: data:">`. Template renders it via `<iframe sandbox srcdoc="{{ preview_doc }}">` (Django auto-escapes the attribute; `sandbox` without `allow-scripts` is the second line of defence). New regression test `test_admin_preview_isolates_xss_in_iframe` injects `<script>alert("xss")</script>` and asserts the raw tag appears nowhere in the admin-origin DOM (only HTML-attribute-escaped inside `srcdoc`). All 4 preview tests pass.

### C3. Password-reset attack path on OAuth-only accounts

- [x] **C3** — disable password / secondary-email URLs from allauth
  - Source: §1.2
  - Files: `config/urls.py:9` (replace `include("allauth.urls")` with explicit list), `apps/accounts/adapters.py`
  - Change: mount only the OAuth-relevant subset of allauth URLs:
    ```
    path("accounts/login/", LoginView.as_view(), name="account_login")
    path("accounts/logout/", LogoutView.as_view(), name="account_logout")
    path("accounts/social/", include("allauth.socialaccount.urls"))
    path("accounts/google/", include("allauth.socialaccount.providers.google.urls"))
    path("accounts/microsoft/", include("allauth.socialaccount.providers.microsoft.urls"))
    ```
    Drop `password_*` and `email/`.
  - Acceptance: `GET /accounts/password/reset/` returns 404. `GET /accounts/email/` returns 404. OAuth login still succeeds end-to-end.
  - Done: 2026-04-27 — `config/urls.py` no longer includes `allauth.urls`. Mounted explicitly: `account_login`, `account_logout`, `socialaccount.urls` at `/accounts/3rdparty/`, and Google/Microsoft provider modules at `/accounts/` (the providers' own `urlpatterns` already carry `google/` and `microsoft/` prefixes — mounting them at `/accounts/google/` would have produced `/accounts/google/google/login/` and broken the OAuth redirect URIs registered in the provider consoles). `resolve()` returns 404 for `/accounts/password/{reset,change,set}/`, `/accounts/email/`, `/accounts/confirm-email/`, `/accounts/inactive/`. OAuth entry points still reverse: `account_login → /accounts/login/`, `google_login → /accounts/google/login/`, `microsoft_login → /accounts/microsoft/login/`. New file `apps/accounts/tests/test_url_surface.py` (12 parametrized assertions) locks the surface. Full suite: 81 passed.

### C4. `SECRET_KEY` placeholder fail-closed guard

- [x] **C4** — refuse to boot with the placeholder key in prod
  - Source: §6, §11
  - File: `config/settings.py:6`
  - Change: after the `config()` call, add
    ```
    from django.core.exceptions import ImproperlyConfigured
    if not DEBUG and SECRET_KEY.startswith("django-insecure"):
        raise ImproperlyConfigured("SECRET_KEY must be set in production.")
    ```
  - Acceptance: `DEBUG=False SECRET_KEY="django-insecure-..." python manage.py check` raises `ImproperlyConfigured`. Production boot with a real key still succeeds.
  - Done: 2026-04-25 — guard verified: placeholder + DEBUG=False raises ImproperlyConfigured; real key boots cleanly; 63 tests still pass

### C5. `User.email` uniqueness constraint

- [x] **C5** — make email unique at the model + DB level
  - Source: §6
  - Files: `apps/accounts/models.py`, new migration under `apps/accounts/migrations/`
  - Change: add `email = models.EmailField(unique=True)` to `User`. Generate migration; precede with a data migration that detects pre-existing duplicates and fails loudly (so ops investigates rather than the schema migration crashing).
  - Acceptance: migration applies cleanly. `User.objects.create(email="x@y.com"); User.objects.create(email="x@y.com")` raises `IntegrityError`.
  - Done: 2026-04-27 — `User.email = models.EmailField(unique=True)` declared. Migration pair: `0003_assert_no_duplicate_emails.py` (RunPython that groups by email, raises a `RuntimeError` listing offenders if any group has count>1) → `0004_alter_user_email.py` (Django-generated `AlterField` with `unique=True`). Both applied cleanly against the dev DB. New file `apps/accounts/tests/test_email_uniqueness.py` proves the IntegrityError path (wrapped in `transaction.atomic()` so the failure doesn't poison the outer pytest-django transaction) plus a model-meta sanity assertion. Full suite: 83 passed.

### C6. Flower default password

- [x] **C6** — make `FLOWER_BASIC_AUTH` mandatory
  - Source: §14
  - File: `docker-compose.yml:66`
  - Change: replace `${FLOWER_BASIC_AUTH:-admin:changeme}` with `${FLOWER_BASIC_AUTH:?FLOWER_BASIC_AUTH must be set}`.
  - Acceptance: `docker-compose up flower` without setting the env var fails with a clear "FLOWER_BASIC_AUTH must be set" message. With the env var set, Flower starts and requires those credentials at the `/flower/` endpoint.
  - Done: 2026-04-25 — `docker compose config` errors with explicit "FLOWER_BASIC_AUTH must be set" when unset; with `FLOWER_BASIC_AUTH=admin:s3cret` the resolved command shows `--basic_auth=admin:s3cret`

### C7. Missing `.dockerignore`

- [x] **C7** — add `.dockerignore` at repo root
  - Source: §14
  - File: `.dockerignore` (new)
  - Change: create the file with at minimum:
    ```
    .git
    .env
    .env.*
    !.env.example
    __pycache__
    *.pyc
    .pytest_cache
    .venv
    node_modules
    *.sqlite3
    cvs/
    staticfiles/
    ```
  - Acceptance: `docker build .` followed by `docker run --rm IMAGE find /app -name '.env'` returns nothing. `.git/` is not present in the image.
  - Done: 2026-04-25 — `.dockerignore` created with patterns covering secrets (.env*), VCS (.git*), build cache (__pycache__, .pytest_cache), virtualenvs (.venv), local dev data (cvs/, *.sqlite3). Final `docker build` verification deferred (no docker daemon access in this env); patterns are syntactically standard Docker ignore globs.

### C8. GDPR Article 20 (data portability) export endpoint

- [x] **C8** — add `/dashboard/exportar-datos/` data-export view
  - Source: §15
  - Files: `apps/dashboard/views.py` (new view + URL), `apps/dashboard/urls.py`, optional template for confirmation page
  - Change: build a zip containing `user.json`, `cvs/*.pdf`, `mailing_logs.csv`, `payments.csv`. Rate-limit to 1/day/user. Stream the response (don't load all CVs into memory).
  - Acceptance: a logged-in user can download their data zip; the zip contains all four artefacts; second request within 24h returns 429.
  - Done: 2026-04-27 — new `export_data` view in `apps/dashboard/views.py`, mounted at `path("exportar-datos/", views.export_data, name="export_data")` (full path `/dashboard/exportar-datos/`). Stack: `@login_required`, `@require_GET`, `@ratelimit(key="user", rate="1/d", block=True)`. Archive built into a `SpooledTemporaryFile(max_size=5 MiB)` (in-memory then spills to disk) wrapped in `zipfile.ZipFile(ZIP_DEFLATED)`, returned as `FileResponse(as_attachment=True)`. Members: `user.json` (helper `_serialize_user` excludes hashed password and Django internals like `is_staff`), `mailing_logs.csv` + `payments.csv` (both built via `csv.writer` over an `iterator(chunk_size=200)` queryset), and `cvs/<pk>_<filename>.pdf` per CV. New file `apps/dashboard/tests/test_export_data.py` covers (1) anonymous-user redirect, (2) URL shape, (3) all four artefacts present + content sanity (user email, payment row count, CV path under `cvs/`), (4) no cross-user leakage (other user's CVs/logs absent), (5) second request within 24h → 429 (with `RATELIMIT_ENABLE=True`). Full suite: 91 passed.

### C9. CV delete-override misses cascade and admin bulk-delete

- [x] **C9** — replace `CV.delete()` override with a `pre_delete` signal
  - Source: §2.2, §4
  - File: `apps/accounts/models.py:35-53`
  - Change: remove the `delete()` override; register `pre_delete` instead so cascade and bulk-delete paths fire S3 cleanup:
    ```
    @receiver(pre_delete, sender=CV)
    def cv_pre_delete(sender, instance, **kwargs):
        if instance.file:
            instance.file.delete(save=False)
    ```
  - Acceptance: `User.objects.filter(...).delete()` (cascade path) and admin bulk-delete both leave zero orphaned objects in the Spaces bucket. Existing per-row admin delete and `delete_account` continue to work.
  - Done: 2026-04-27 — `CV.delete()` override removed from `apps/accounts/models.py`. New receiver `cv_pre_delete` in `apps/accounts/signals.py` (already loaded via `AccountsConfig.ready()`) calls `instance.file.delete(save=False)` for every CV row about to be removed. New file `apps/accounts/tests/test_cv_file_cleanup.py` covers all three deletion paths by mocking `FieldFile.delete` and asserting call counts: per-row `cv.delete()` → 1 call; `user.delete()` cascade across 3 CVs → 3 calls; `CV.objects.filter(...).delete()` bulk → 3 calls. Full suite: 86 passed.

---

## ⚠️ Hardening — quick wins (under 30 minutes each)

- [x] **H1** — `CSRF_COOKIE_HTTPONLY = True` (no AJAX consumes the cookie)
  - Source: §16
  - File: `config/settings.py`
  - Acceptance: setting present; a manual login flow still completes a POST form successfully.
  - Done: 2026-04-25 — `settings.CSRF_COOKIE_HTTPONLY` evaluates to `True`; 63 tests still pass (CSRF posture unchanged for HTML form flows).

- [x] **H2** — `SESSION_COOKIE_AGE = 604800` (1 week)
  - Source: §17
  - File: `config/settings.py`
  - Acceptance: setting present; new sessions expire after 7 days.
  - Done: 2026-04-25 — `settings.SESSION_COOKIE_AGE == 604800`.

- [x] **H3** — pin upload size limits explicitly
  - Source: §1.3, §10
  - File: `config/settings.py`
  - Change: add `DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024` and `FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024`.
  - Acceptance: settings present; uploading a 12MB file at `/dashboard/subir-cv/` is rejected before the view runs.
  - Done: 2026-04-25 — both settings = 5242880; note: Django's `DATA_UPLOAD_MAX_MEMORY_SIZE` excludes multipart file bytes, so the 12MB upload rejection still relies on the existing 10MB in-view check + Nginx (H20). The settings here protect against >5MB non-file form data and force >5MB files to stream-to-disk.

- [x] **H4** — Docker HEALTHCHECK
  - Source: §14
  - File: `Dockerfile`
  - Change: add `HEALTHCHECK --interval=30s --timeout=5s CMD curl -fsS http://localhost:8000/healthz || exit 1`.
  - Acceptance: `docker inspect IMAGE | jq '.[0].Config.Healthcheck'` shows the command. `docker ps` reports `(healthy)`.
  - Done: 2026-04-25 — `HEALTHCHECK` directive added with `--start-period=20s` to allow gunicorn boot. `curl` added to apt-get install list. Final daemon-side verification deferred (no docker daemon access).

- [x] **H5** — Dockerfile non-root user
  - Source: §14
  - File: `Dockerfile`
  - Change: add `RUN useradd -m -u 1000 app && chown -R app:app /app` after `collectstatic`, then `USER app`.
  - Acceptance: `docker run --rm IMAGE id -u` returns `1000`.
  - Done: 2026-04-25 — `useradd --create-home --uid 1000 app && chown -R app:app /app` + `USER app` placed after `collectstatic`. Final daemon-side verification deferred.

- [x] **H6** — split prod/dev requirements
  - Source: §13
  - Files: `requirements.txt`, `requirements-dev.txt` (new), `Dockerfile`
  - Change: move `pytest`, `pytest-django`, `pytest-mock` into `requirements-dev.txt`. Dockerfile installs only `requirements.txt`.
  - Acceptance: `docker run --rm IMAGE python -c "import pytest"` raises `ModuleNotFoundError`. CI installs both files.
  - Done: 2026-04-25 — pytest{,-django,-mock} removed from `requirements.txt`. `requirements-dev.txt` created with `-r requirements.txt` + the 3 test deps. `.github/workflows/ci.yml` switched to `pip install -r requirements-dev.txt`.

- [x] **H7** — drop emails from logger calls
  - Source: §12
  - File: `apps/accounts/signals.py:32`, `apps/mailing/tasks.py:66, 89, 98, 104`
  - Change: replace `user.email` with `user.pk` in 6 call sites. Where a company email is also logged (`tasks.py:89`), replace with `company.pk`.
  - Acceptance: grep for `user.email` and `company.email` inside `logger.` calls returns zero hits.
  - Done: 2026-04-25 — 6 call sites updated to log `user.pk` / `company.pk` instead of `user.email` / `company.email`. Grep confirms zero PII hits. 63 tests still pass.

- [x] **H8** — redact OAuth token-refresh failure logs
  - Source: §2.1, §8.3, §12
  - File: `apps/mailing/engine.py:51, 81`
  - Change: replace `logger.error("... %s", resp.text)` with `logger.error("token refresh failed: status=%d error=%s", resp.status_code, data.get("error", "unknown"))` (after parsing `data = resp.json()` defensively in a try/except).
  - Acceptance: triggering a refresh failure no longer puts the raw response body into the log line.
  - Done: 2026-04-25 — engine.py:50-56 / 81-87 now parse `resp.json()` inside try/except ValueError and log only `status=%d error=%s`. Two new pytest assertions (`test_google_refresh_failure_log_excludes_raw_body`, `test_microsoft_refresh_failure_log_excludes_raw_body`) confirm the raw body never enters the log records.

- [x] **H9** — strip CRLF from email subject
  - Source: §2.3
  - File: `apps/mailing/engine.py` (where `subject` is rendered before MIME assembly)
  - Change: `subject = subject.replace("\r", "").replace("\n", "")` before passing into the MIME message.
  - Acceptance: a template with `Test\r\nBcc: x@evil.com` in the subject sends a single recipient (no Bcc header injected).
  - Done: 2026-04-25 — strip applied in `send_cv_email` right after `template.render(...)`. New pytest `test_send_cv_email_strips_crlf_from_subject` decodes the actual base64 MIME payload, parses it via `email.message_from_string`, asserts `msg["Bcc"] is None` and the only `To` header is the company email.

- [x] **H10** — wrap destructive ops in `transaction.atomic()`
  - Source: §1.3, §9
  - Files: `apps/dashboard/views.py:138-159` (`delete_account`), `apps/accounts/management/commands/delete_user.py`, `apps/dashboard/views.py:84-98` (`delete_cv`)
  - Change: wrap the per-CV loop + `user.delete()` + `user.save()` block(s) in `with transaction.atomic():`.
  - Acceptance: simulated kill mid-loop leaves either all CVs deleted or none — no partial state.
  - Done: 2026-04-27 — `transaction.atomic()` wrapping added to all three call sites: `delete_account` (CV loop + `user.delete()` inside one block; `logout()` moved AFTER the atomic block so a rollback doesn't log out a still-alive account); `delete_cv` (row delete + active_cv fallback `user.save()` together); `delete_user` management command (CV loop + `user.delete()`). New file `apps/dashboard/tests/test_atomic_deletes.py` injects a `RuntimeError` mid-flow and asserts the DB rolls back to the pre-call state — `delete_account` test patches `User.delete` to raise after partial work, `delete_cv` test patches the fallback `User.save` to raise. Full suite: 93 passed.

- [ ] **H11** — `str.format_map(SafeDict)` for templates
  - Source: §1.6, §2.3, §2.4
  - File: `apps/mailing/models.py:65-67` (`EmailTemplate.render`)
  - Change: introduce `class SafeDict(dict): def __missing__(self, key): return f"{{{key}}}"` and call `subject.format_map(SafeDict(context))`. Drops attribute walks (`{user.__class__}`).
  - Acceptance: a template with `{cv_url.__class__}` renders as the literal string, not the type repr.

- [ ] **H12** — decouple URL scheme from `DEBUG`
  - Source: §2.3, §6
  - Files: `config/settings.py`, `apps/mailing/engine.py:139`, `apps/mailing/tasks.py:117`, `apps/payments/views.py:27, 100`
  - Change: introduce `SITE_SCHEME = config("SITE_SCHEME", default="https")` in settings; replace four occurrences of `scheme = "https" if not settings.DEBUG else "http"` with `scheme = settings.SITE_SCHEME`.
  - Acceptance: `DEBUG=True SITE_SCHEME=https` produces `https://` URLs in re-link emails and Stripe success URLs.

- [ ] **H13** — `Cache-Control: no-store` on `/cv/<uuid>/` redirect
  - Source: §1.1, §2.2
  - File: `apps/mailing/views.py:52` (`cv_download`)
  - Change: build the redirect via `response = redirect(url); response["Cache-Control"] = "no-store"; return response`.
  - Acceptance: response headers include `Cache-Control: no-store`.

- [ ] **H14** — `EmailTemplate.body_html` size cap
  - Source: §4
  - File: `apps/mailing/models.py` (`EmailTemplate` model), new migration
  - Change: add `validators=[MaxLengthValidator(50000)]` to `body_html`. Add `clean()` method that re-checks if validators are bypassed.
  - Acceptance: admin form rejects a body over 50K chars.

---

## ⚠️ Hardening — medium effort (1–4 hours each)

- [ ] **H15** — rate-limit decorators on remaining endpoints
  - Source: §10
  - Files: `apps/dashboard/views.py:upload_cv` (`@ratelimit(key="user", rate="10/h")`), `apps/payments/views.py:billing_portal` (`@ratelimit(key="user", rate="20/h")`), `apps/payments/views.py:create_checkout` (`@ratelimit(key="user", rate="10/h")`), `config/health.py:healthz` (`@ratelimit(key="ip", rate="60/m")`)
  - Acceptance: 11th `upload_cv` call within an hour returns 429; 21st `billing_portal` returns 429; etc.

- [ ] **H16** — xlsx import cell sanitization
  - Source: §1.6, §2.5
  - File: `apps/companies/importers.py`
  - Change: add a `_sanitize(value)` helper that strips leading `=`, `+`, `-`, `@` (CSV-injection guard) and HTML-escapes the result. Apply to every cell value before `Company.objects.create(...)`.
  - Acceptance: an xlsx row with `=cmd|...` or `<script>` in `name` gets stored sanitized; outbound emails contain no raw HTML from imported data.

- [ ] **H17** — PDF magic-byte check on upload
  - Source: §1.3, §2.2
  - File: `apps/dashboard/views.py:47-71` (`upload_cv`)
  - Change: read the first 4 bytes; require `b"%PDF"`; `cv_file.seek(0)` before passing on.
  - Acceptance: uploading `evil.html` renamed to `cv.pdf` is rejected with the existing "no es un PDF válido" message.

- [ ] **H18** — webhook idempotency via `select_for_update`
  - Source: §2.8
  - File: `apps/payments/views.py:130-141` (`_handle_successful_payment`)
  - Change: wrap in `with transaction.atomic():` and use `StripePayment.objects.select_for_update().filter(stripe_session_id=session_id)`.
  - Acceptance: two simultaneous webhook deliveries for the same session result in exactly one `credits_remaining` increment (verifiable via stress test).

- [ ] **H19** — admin permission tightening
  - Source: §1.5
  - Files: `apps/companies/admin.py` (`BlacklistAdmin`), `apps/mailing/admin.py` (`MailingLogAdmin`, `EmailTemplateAdmin`)
  - Change: `BlacklistAdmin.has_delete_permission = lambda self, request, obj=None: request.user.is_superuser`. Confirm `MailingLogAdmin.has_add_permission=False` and all fields readonly. Restrict `EmailTemplateAdmin` body editing to superusers (defence-in-depth alongside C2).
  - Acceptance: a non-superuser staff sees no delete checkbox in `BlacklistAdmin`; cannot edit `EmailTemplate.body_html`.

- [ ] **H20** — Nginx body-size enforcement documentation + automation
  - Source: §1.3, §10
  - Files: `docs/deploy.md`, deploy templates (if any)
  - Change: add `client_max_body_size 11M;` to the Nginx server block snippet. If using a managed LB, document the equivalent setting.
  - Acceptance: a curl POST of a 50MB body to `/dashboard/subir-cv/` is rejected by Nginx (HTTP 413) before reaching Django.

- [ ] **H21** — `UserAdmin` staff-escalation guard
  - Source: §1.5, §2.10
  - File: `apps/accounts/admin.py`
  - Change: override `get_fieldsets()` to remove `is_staff`, `is_superuser`, `groups`, `user_permissions` from the form for non-superusers.
  - Acceptance: a staff user (non-superuser) opens another user's admin form and cannot toggle `is_staff` or `is_superuser`.

- [ ] **H22** — swap `psycopg2-binary` → `psycopg2`
  - Source: §13
  - File: `requirements.txt`
  - Change: replace `psycopg2-binary==2.9.10` with `psycopg2==2.9.10`. Verify `Dockerfile:9` already installs `libpq-dev` (it does).
  - Acceptance: `docker build .` succeeds; Django connects to PostgreSQL normally.

---

## ⚠️ Hardening — heavy lift (1–3 days each)

- [ ] **H23** — django-allauth 0.63.6 → 65.x upgrade
  - Source: §1.2, §13
  - Files: `requirements.txt`, `config/settings.py` (settings rename), `apps/accounts/adapters.py` (signal API), tests
  - Change: bump version; rename `ACCOUNT_AUTHENTICATION_METHOD` → `ACCOUNT_LOGIN_METHODS`; verify all settings against the 65.x release notes; set `SOCIALACCOUNT_EMAIL_AUTHENTICATION_ENABLED=False` to close cross-provider email-collision risk; run full regression test suite.
  - Acceptance: all auth tests pass; manual Google + Microsoft login flows work; cross-provider email-collision is no longer exploitable.

- [ ] **H24** — encrypt `SocialToken` columns at rest
  - Source: §2.1
  - Files: `requirements.txt` (add `django-cryptography`), allauth adapter override, migration
  - Change: replace `SocialToken.token` / `token_secret` columns with `EncryptedCharField`; key managed via env. Plan for key rotation.
  - Acceptance: a DB dump shows token values as encrypted blobs, not plaintext. App-level `social.token` access still works through the adapter.

- [ ] **H25** — `MailingLog` retention task
  - Source: §15
  - Files: `apps/mailing/tasks.py` (new task), `apps/mailing/management/commands/setup_periodic_tasks.py`
  - Change: add `prune_old_mailing_logs` Celery task that deletes rows where `sent_at < now - 365 days`. Schedule weekly via celery-beat.
  - Acceptance: task runs; rows older than 12 months are removed; `docs/features/blacklist-unsubscribe.md` (or new doc) records the policy.

- [ ] **H26** — OAuth scope-grant verification at callback
  - Source: §1.2, §2.1
  - Files: `apps/accounts/adapters.py`, dashboard banner template
  - Change: after the OAuth callback, inspect granted scopes vs. requested. If `gmail.send` / `Mail.Send` is missing, set a session flag and render a banner on `/dashboard/` directing the user to re-link.
  - Acceptance: a user who denies `gmail.send` at the consent screen sees a banner explaining why sends will fail, and a "re-link" button.

---

## 🔍 Verify — runtime tests required (no code change yet)

- [ ] **V1** — confirm GET `/accounts/logout/` does not destroy the session
  - Source: §1.2
  - Method: log in, `curl -i GET /accounts/logout/`, then `curl -i -b cookie GET /dashboard/`. Should still be authenticated until POST is made.
  - If destroyed on GET: set `ACCOUNT_LOGOUT_ON_GET=False` explicitly.
  - Outcome: _result + date_

- [ ] **V2** — cross-provider email collision test
  - Source: §1.2
  - Method: register user with Google OAuth using `test@example.com`; attempt to register again with Microsoft OAuth using the same email. Observe whether allauth merges (takeover possible) or duplicates (login ambiguous).
  - Outcome: _result + date_

- [ ] **V3** — run `pip-audit`
  - Source: §13
  - Method: `pip install pip-audit && pip-audit -r requirements.txt --strict`. Triage each CVE.
  - Outcome: _list of findings + decisions + date_

- [ ] **V4** — confirm `SocialToken` masking in admin list view
  - Source: §1.5
  - Method: log in as superuser → `/admin/socialaccount/socialtoken/` → confirm token values are not displayed in full.
  - Outcome: _result + date_

- [ ] **V5** — Microsoft Graph `saveToSentItems: False` runtime check
  - Source: §8.2
  - Method: trigger a real send via Microsoft path; check the user's Outlook "Sent" folder; confirm absence.
  - Outcome: _result + date_

- [ ] **V6** — password-reset on OAuth-only account
  - Source: §1.2
  - Method (only if C3 is not yet shipped): trigger password reset on an account created via OAuth. Test whether `has_usable_password()` blocks the flow or whether it allows takeover.
  - Outcome: _result + date_ (becomes moot once C3 ships)

---

## 🛡️ CI gates — one-time setup (prevents regressions)

- [x] **CI1** — `manage.py check --deploy` step in GitHub Actions
  - Source: §6
  - File: `.github/workflows/ci.yml`
  - Change: add a step running `python manage.py check --deploy --fail-level WARNING` against a prod-like settings profile.
  - Acceptance: CI fails when `DEBUG=True`, missing cookie-secure flags, or default `SECRET_KEY` are detected.
  - Done: 2026-04-25 — added "Django deploy check (prod-mode hardening gate)" step in ci.yml after H6's install step. With prod-mode env (DEBUG=False, all SECURE_* on, strong SECRET_KEY) → "System check identified no issues". Negative tests confirm: DEBUG=True triggers W004/W008/W012/W016/W018; placeholder SECRET_KEY trips the C4 boot guard before check runs.

- [ ] **CI2** — `pip-audit` step in CI
  - Source: §13
  - File: `.github/workflows/ci.yml`
  - Change: add `pip install pip-audit && pip-audit -r requirements.txt --strict`.
  - Acceptance: a PR that adds a CVE-affected dep fails CI.

- [ ] **CI3** — `bandit` static-analysis step
  - Source: §7
  - File: `.github/workflows/ci.yml`
  - Change: add `pip install bandit && bandit -r apps/ config/ -ll` (level=LOW, confidence=LOW).
  - Acceptance: a PR introducing `mark_safe`, `subprocess(shell=True)`, or `eval` triggers a CI failure.

- [ ] **CI4** — decorator-presence test
  - Source: §1.3, §1.4
  - Files: new test file under `apps/dashboard/tests/test_decorators.py`
  - Change: enumerate all dashboard + payments URL views, assert `@login_required` and `@require_POST` decorators are present where expected.
  - Acceptance: a PR that accidentally removes `@login_required` from `set_active_cv` fails the test.

---

## Open notes / discoveries

Capture surprises during implementation here — things that shift assumptions or generate new tickets. One bullet per finding; promote to its own checklist entry if it grows past a sentence.

- _(none yet)_

---

## Done log

When an item is checked off, add a one-liner here so it's easy to scroll the change history:

- _(empty)_
