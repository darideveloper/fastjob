# Security Check — Project Inventory

Exhaustive list of every surface that needs to be reviewed before a security audit. Each item names **what** to check and **where** (file path / URL / model). No findings yet — this is the checklist that drives the actual testing pass.

> Scope: ResumeLink (Django 4.2 + Celery + PostgreSQL + Redis + Stripe + Google/Microsoft OAuth + DigitalOcean Spaces). Generated 2026-04-24.

---

## 1. HTTP routes — all URL entry points

Every route the server accepts. Testers should enumerate these first and verify auth, CSRF, method restrictions, rate limiting, and input validation.

### 1.1 Public / unauthenticated routes (highest risk — no identity bound)

| URL | View | File | Check |
|---|---|---|---|
| `GET /` | `TemplateView home.html` | `config/urls.py:14` | Info disclosure in rendered HTML; leaked env values in template |
| `GET /healthz` | `healthz` | `config/health.py` | Info leak (status JSON), rate limiting (unbounded polling = amplification), unauthenticated access is intentional — confirm nothing sensitive in response |
| `GET /cv/<uuid:token>/` | `cv_download` | `apps/mailing/views.py:19` | UUID guessability, rate limit (currently 30/h/IP), pre-signed URL construction, direct object reference, cache headers / referer leakage |
| `GET /unsubscribe/<uuid:token>/` | `unsubscribe` | `apps/mailing/views.py:58` | Rate limit (currently 10/h/IP), CSRF on GET (state-changing GET — anti-pattern), idempotency, email-enumeration via behavior diff |
| `POST /payments/webhook/` | `stripe_webhook` | `apps/payments/views.py` | `@csrf_exempt` — signature verification, replay protection, body-size limit, timing attacks on signature compare, error swallowing |

**Verdicts:**

- `GET /` — ✅ **OK.** `templates/home.html` is fully static (no `|safe` / `mark_safe` / `autoescape off`); `templates/base.html` only renders `user.email` and `user.credits_remaining` under default auto-escape. No env values reach the template. The hard-coded `next=/dashboard/` on the homepage CTA links is safe — not user-controlled.
- `GET /healthz` — ⚠️ **Hardening opportunity.** No `@ratelimit` decorator on this endpoint (`config/health.py`). Each request is cheap (one `SELECT 1` + a 5-byte cache round-trip), so amplification is bounded, but consider a coarse 60/min/IP cap at the load balancer or via `@ratelimit(key="ip", rate="60/m")`. JSON body itself contains no sensitive info — safe.
- `GET /cv/<uuid:token>/` — ✅ **OK** for brute-force / IDOR (UUID4 = 122 bits + 30/h/IP rate limit makes enumeration infeasible). ⚠️ **Hardening:** the 302 redirect response has no `Cache-Control: no-store`/`Pragma: no-cache` — a shared corporate proxy could in theory cache the redirect target (the pre-signed Spaces URL) within its 5-minute TTL window. Pre-signed URL construction itself looks correct (`apps/mailing/views.py:35-50`).
- `GET /unsubscribe/<uuid:token>/` — ⚠️ **Known design quirk, not a vulnerability.** State-changing GET is intentional (per `docs/features/blacklist-unsubscribe.md`) so it works from email-client renderers, but link prefetchers, antivirus scanners, and Outlook Safe Links **will** trigger the blacklist. `get_or_create` is idempotent, so duplicate triggers are no-ops. Rate-limited at 10/h/IP. UUID4 entropy makes token enumeration impractical. Timing-based email enumeration: theoretically possible (404 path is shorter than the `get_or_create` path), but the attacker would need to know a valid token first — circular.
- `POST /payments/webhook/` — ✅ **OK.** `stripe.Webhook.construct_event` does the HMAC signature check (Stripe SDK uses `hmac.compare_digest` internally — constant-time). `_handle_successful_payment` is idempotent via `payment.status == COMPLETED` early-return at `apps/payments/views.py:98-99`. Unknown event types return HTTP 200 without action — correct. ⚠️ **Hardening:** no explicit body-size cap beyond Django's default `DATA_UPLOAD_MAX_MEMORY_SIZE=2.5MB`; Stripe payloads are typically <10KB so this is fine in practice but worth pinning explicitly.

### 1.2 Allauth-provided routes

Mounted under `/accounts/` via `path("accounts/", include("allauth.urls"))` — `config/urls.py:9`. Inherits allauth's URL tree; each merits a scan:

| Path | Purpose | Check |
|---|---|---|
| `/accounts/login/` | Social login entry | Open redirect in `next=` param, CSRF, session fixation |
| `/accounts/logout/` | Session termination | CSRF, logout on GET (anti-pattern), session invalidation |
| `/accounts/signup/` | Signup (OAuth only) | `SOCIALACCOUNT_AUTO_SIGNUP=True` → account takeover if email spoofed |
| `/accounts/google/login/` | Google OAuth start | State/nonce handling |
| `/accounts/google/login/callback/` | Google OAuth return | State validation, code injection, downgrade to no-`gmail.send` scope |
| `/accounts/microsoft/login/` | Microsoft OAuth start | Same |
| `/accounts/microsoft/login/callback/` | Microsoft OAuth return | Same |
| `/accounts/social/connections/` | Manage linked accounts | CSRF on unlink; triggers `social_account_removed` signal |
| `/accounts/password/*` | Password reset / change | We don't use passwords but allauth still exposes these routes — ensure they're effectively dead or disabled |
| `/accounts/email/` | Email management | Adding a secondary email → account takeover vector |

**Verdicts:**

- `/accounts/login/` — ✅ **Open redirect mitigated.** Django + allauth validate `next=` via `url_has_allowed_host_and_scheme` against `ALLOWED_HOSTS`. CSRF on GET-init: see below. Session fixation: allauth rotates the session key on successful login (default behavior).
- `/accounts/logout/` — ⚠️ **Default allauth behavior renders a confirmation page on GET, then POST to actually log out.** No `ACCOUNT_LOGOUT_ON_GET` set in `config/settings.py`, so we get the safe two-step flow. Confirm at runtime that the GET path doesn't already destroy the session.
- `/accounts/signup/` — ⚠️ **Cross-provider email collision risk.** Config: `SOCIALACCOUNT_AUTO_SIGNUP=True` + `ACCOUNT_EMAIL_VERIFICATION="none"` means allauth trusts the email returned by the IdP. Google does verify owner-of-email server-side, so Google→Google is safe. **Microsoft's email verification depends on tenant configuration** — a personal-Microsoft-account user could in theory register an unverified email that collides with an existing Google-linked user, leading to auto-link / takeover. Mitigation: set `SOCIALACCOUNT_EMAIL_VERIFICATION="mandatory"` for Microsoft, or set `SOCIALACCOUNT_EMAIL_AUTHENTICATION_ENABLED=False`. 🔍 Needs runtime test against real Microsoft tenants to confirm exposure.
- `/accounts/google/login/` & `/accounts/microsoft/login/` — ✅ Allauth handles state/nonce. `SOCIALACCOUNT_LOGIN_ON_GET=True` means an attacker can `<img src=".../accounts/google/login/">` to force OAuth start, but the worst outcome is the victim ends up logged into *their own* account — no takeover.
- `/accounts/google/login/callback/` & `/accounts/microsoft/login/callback/` — ✅ State param validation handled by allauth. ⚠️ **Scope downgrade not detected at login time:** if a user denies the `gmail.send` / `Mail.Send` scope at the consent screen, allauth completes login with whatever scopes were granted; sends will then fail at runtime with a Gmail/Graph 403. Acceptable but worth surfacing — current code logs `MailingLog.status=FAILED`, doesn't notify the user.
- `/accounts/social/connections/` — ✅ Allauth requires POST + CSRF token for disconnect. The `social_account_removed` signal handler (`apps/accounts/signals.py:21-28`) auto-pauses the campaign — confirmed.
- `/accounts/password/*` — ❌ **Concern: password-reset attack path is enabled.** `AUTHENTICATION_BACKENDS` includes `ModelBackend` (`config/settings.py:106-109`), and allauth's password URLs are mounted by `include("allauth.urls")`. OAuth-created users have `set_unusable_password()` by default, but allauth's password-reset flow may still allow setting a usable one. **Net effect:** anyone with access to a victim's email inbox can set a password and bypass the OAuth flow entirely (login via `username/password` backend). For Google/Microsoft users this is no worse than existing OAuth (since the attacker would need email access to complete OAuth too), but it's an unnecessary additional path. 🔍 Needs runtime test: trigger password reset on an OAuth-only account, verify whether `has_usable_password()` blocks the flow or whether it goes through. Recommend either removing the password URLs or setting `ACCOUNT_ADAPTER` to override `is_open_for_signup` / disable password reset.
- `/accounts/email/` — ⚠️ **Adding secondary email auto-verifies under `ACCOUNT_EMAIL_VERIFICATION="none"`.** An attacker who has session access (via XSS or cookie theft) could add their own email as a secondary, then trigger password reset on that secondary. Same root cause as `/accounts/password/*`. Mitigation: set `ACCOUNT_EMAIL_VERIFICATION="mandatory"` *or* disable email-management URLs.

### 1.3 Authenticated user routes (`/dashboard/*`)

All require `@login_required`. Verify each:

| URL | Method | View | File | Check |
|---|---|---|---|---|
| `/dashboard/` | GET | `index` | `apps/dashboard/views.py:19` | IDOR via `?page=`, info leak in logs, HTML injection in company names |
| `/dashboard/subir-cv/` | POST | `upload_cv` | `apps/dashboard/views.py:47` | MIME vs. extension check, size limit enforcement, path traversal in filename, storage exhaustion, polyglot files, zip bombs, content sniffing |
| `/dashboard/cv/<int:cv_id>/activar/` | POST | `set_active_cv` | `apps/dashboard/views.py:75` | **IDOR** — ensure `user=request.user` filter present; integer enumeration |
| `/dashboard/cv/<int:cv_id>/eliminar/` | POST | `delete_cv` | `apps/dashboard/views.py:82` | IDOR, CSRF, race condition with `active_cv` re-pointing |
| `/dashboard/filtros/` | POST | `update_filters` | `apps/dashboard/views.py:96` | Input length, stored XSS via filter values rendered in admin |
| `/dashboard/campana/` | POST | `toggle_campaign` | `apps/dashboard/views.py:104` | Guard bypass (credits/CV/provider), CSRF |
| `/dashboard/eliminar-cuenta/` | GET/POST | `delete_account` | `apps/dashboard/views.py:128` | CSRF on destructive op, case-sensitivity of email match, session invalidation after delete, cascade completeness (CVs, tokens, logs) |

**Verdicts:**

- `GET /dashboard/` — ✅ **OK.** `MailingLog.objects.filter(user=user)` correctly scopes the queryset. `?page=N` is fed to Django's `Paginator.get_page()` which gracefully handles bad input. All template renders use auto-escape (`{{ log.company_email_snapshot }}`, `{{ log.email_template.name }}`). No user-controlled HTML reaches the page.
- `POST /dashboard/subir-cv/` — ⚠️ **Multiple hardening gaps.** (1) Validation is **extension-only** (`cv.name.lower().endswith(".pdf")`); no MIME check, no magic-byte sniff. A user can upload `evil.pdf` containing HTML — the recipient's browser may render it depending on `Content-Type` returned by Spaces (Spaces auto-detects from extension, so this is mostly mitigated). (2) **No per-user CV count limit** — a malicious user can call `upload_cv` repeatedly to fill the Spaces bucket. (3) **Size limit (10MB) enforced in Python after upload** — Django reads the entire body into memory before the check; consider `DATA_UPLOAD_MAX_MEMORY_SIZE` + Nginx `client_max_body_size`. (4) Path traversal in filename: blocked by `django-storages` (the `name` is regenerated server-side, `AWS_S3_FILE_OVERWRITE=False`). ✅
- `POST /dashboard/cv/<int:cv_id>/activar/` — ✅ **IDOR mitigated.** `get_object_or_404(CV, pk=cv_id, user=request.user)` at `apps/dashboard/views.py:76` correctly scopes to the requesting user. CSRF: `@require_POST` + Django's CsrfViewMiddleware default protection.
- `POST /dashboard/cv/<int:cv_id>/eliminar/` — ✅ **IDOR mitigated** (same pattern). ⚠️ **Race condition window:** between `cv.delete()` and the `request.user.save(update_fields=["active_cv", "is_campaign_active"])`, a Celery worker iterating `active_users` could observe an inconsistent state. Bounded by transaction isolation; in practice the next tick recovers. Consider wrapping in `transaction.atomic()`.
- `POST /dashboard/filtros/` — ✅ **OK.** `area_filter`/`location_filter` are `CharField(max_length=200)` and rendered with default auto-escape on dashboard + admin form. No XSS path. **One quirk:** Django doesn't enforce `max_length` on `save()` (only `full_clean()`), so a user can store >200 chars by bypassing form validation — but the `.strip()` happens in Python and `request.POST.get(...)` returns Python strings of arbitrary length. PostgreSQL will reject at the column level. ✅
- `POST /dashboard/campana/` — ✅ **OK.** All three guards (`has_cv`, `credits_remaining > 0`, `linked_provider`) re-checked at view level; engine independently re-checks all three in its DB query, so even a guard-bypass in the view (e.g. via direct DB manipulation) wouldn't cause unauthorized sends.
- `GET/POST /dashboard/eliminar-cuenta/` — ✅ **OK.** Email match is case-insensitive (`.lower()` on both sides at `apps/dashboard/views.py:140`). `logout(request)` is called *before* `user.delete()` (line 152), correctly invalidating the session. Cascade completeness: the view iterates `for cv in user.cvs.all(): cv.delete()` to fire the overridden `CV.delete()` (which removes the S3 object) **before** `user.delete()` triggers the bulk SQL DELETE that wouldn't run per-object hooks. `MailingLog`, `SocialAccount`, `SocialToken` cascade via FK; `StripePayment.user = SET_NULL` preserves payment audit. Verified correct.

### 1.4 Authenticated payment routes (`/payments/*`)

| URL | Method | View | File | Check |
|---|---|---|---|---|
| `/payments/paquetes/` | GET | `packages` | `apps/payments/views.py:16` | Info leak on inactive packages |
| `/payments/checkout/<int:package_id>/` | POST | `create_checkout` | `apps/payments/views.py:23` | IDOR across packages (fine — all public); price manipulation via metadata; `success_url`/`cancel_url` open redirect; `customer_email` spoofing |
| `/payments/success/` | GET | `payment_success` | `apps/payments/views.py:63` | `session_id` query param → IDOR (can't view another user's — verify filter); info leak |
| `/payments/portal/` | POST | `billing_portal` | `apps/payments/views.py:74` | Customer lookup by email — email spoofing post-change, caching correctness |

**Verdicts:**

- `GET /payments/paquetes/` — ✅ **OK.** Filters `CreditPackage.objects.filter(is_active=True)` — inactive packages can't be enumerated. `description` is admin-authored, rendered with default auto-escape.
- `POST /payments/checkout/<int:package_id>/` — ✅ **No price manipulation.** `unit_amount=package.price_cents` is read from the DB after `get_object_or_404(CreditPackage, pk=package_id, is_active=True)`. The user controls only `package_id` via URL — they can pick which active package to buy, but cannot override price or credit count. `success_url`/`cancel_url` use `settings.SITE_DOMAIN` (server-controlled, not `Host` header), so no open redirect via header injection. ⚠️ **`scheme = "https" if not settings.DEBUG else "http"` couples scheme to `DEBUG` flag** — a misconfigured prod with `DEBUG=True` would emit `http://` redirect URLs (Stripe accepts these but they leak session params). Already noted in §6. `customer_email=request.user.email` is server-side; no spoofing.
- `GET /payments/success/` — ✅ **IDOR mitigated.** `StripePayment.objects.filter(stripe_session_id=session_id, user=request.user).first()` correctly filters by the requesting user. A user passing another user's `session_id` gets `payment=None` (success page renders generically). No PII leak.
- `POST /payments/portal/` — ⚠️ **Two hardening gaps.** (1) **No `@ratelimit`** on the endpoint — a logged-in user can spam this view to repeatedly call `stripe.Customer.list(email=...)`, consuming Stripe API quota and potentially triggering rate-limit penalties from Stripe against our account. (2) **Email cache stickiness:** `request.user.stripe_customer_id` is cached on first hit and never re-validated. If an admin changes `user.email` post-payment, the cached `customer_id` still points at the original Stripe customer (which arguably is correct behavior, but worth documenting). `return_url` uses `settings.SITE_DOMAIN` — not request-controlled, ✅.

### 1.5 Admin routes (`/admin/*`)

Entire Django admin tree. Mounted at `config/urls.py:8`. Each registered ModelAdmin is its own surface:

| Admin | File | Check |
|---|---|---|
| `accounts.UserAdmin` (+ `CVInline`) | `apps/accounts/admin.py` | Staff escalation, editable fields vs. readonly (OAuth tokens must never be editable), search field SQL safety |
| `accounts.CVAdmin` | `apps/accounts/admin.py` | Staff can view/delete any CV — confirm that's the intent; file link leak |
| `companies.CompanyAdmin` | `apps/companies/admin.py` | Excel import endpoint (see §1.6), search injection |
| `companies.BlacklistAdmin` | `apps/companies/admin.py` | Unsubscribe bypass by deleting blacklist rows — audit trail |
| `mailing.SystemSettingsAdmin` | `apps/mailing/admin.py` | Singleton delete protection, `has_add_permission` on existing rows |
| `mailing.EmailTemplateAdmin` | `apps/mailing/admin.py` | **Custom preview URL** (see §1.6), HTML stored in `body_html` rendered with `mark_safe` — template injection if admin is compromised |
| `mailing.MailingLogAdmin` | `apps/mailing/admin.py` | Read-only enforcement, `has_add_permission=False`, search injection via `company_email_snapshot` |
| `payments.CreditPackageAdmin` | `apps/payments/admin.py` | Price mutation → check if it affects future vs. past charges |
| `payments.StripePaymentAdmin` | `apps/payments/admin.py` | Read-only? Verify. Sensitive IDs (`stripe_payment_intent`) exposed only to staff |
| `allauth.SocialAccount` + `SocialToken` admin | third-party | OAuth tokens masked in list view, editable permissions |

**Verdicts:**

- `accounts.UserAdmin` (+ `CVInline`) — ✅ **OAuth tokens not editable here** (they live under allauth's separate `SocialToken` admin). ⚠️ **Staff escalation:** the inherited `BaseUserAdmin.fieldsets` includes `is_staff`/`is_superuser`/`is_active` toggles → any staff member with `auth.change_user` perm can promote themselves or others. Standard Django default; mitigate by removing those fields from the form for non-superusers via `get_fieldsets()`. Search fields use ORM `icontains` — no SQL injection.
- `accounts.CVAdmin` — ⚠️ **Staff can view any user's CV** (intended for support, but worth confirming). The `file` column generates a pre-signed Spaces URL via `S3Boto3Storage.url()` (5-min TTL) — admins effectively download CVs through their browser session. No bulk-export protection. `CV.delete()` override fires on per-row admin delete; **bulk delete actions in admin use queryset `.delete()` which skips per-object methods** — orphaned S3 objects possible. ⚠️
- `companies.CompanyAdmin` — ✅ **OK.** Standard ORM-backed search, no raw SQL. Custom import URL evaluated separately in §1.6.
- `companies.BlacklistAdmin` — ⚠️ **No audit trail on blacklist deletion.** A malicious or compromised staff account can delete blacklist rows, allowing future emails to land on previously-opted-out companies (compliance risk under CAN-SPAM / GDPR opt-out). Mitigate by overriding `has_delete_permission` to return False, *or* adding a Django admin LogEntry inspection.
- `mailing.SystemSettingsAdmin` — ✅ **OK.** `has_delete_permission=False`, `has_add_permission` returns `not SystemSettings.objects.exists()` — singleton invariant enforced. `pk=1` enforced in model `save()` override.
- `mailing.EmailTemplateAdmin` — ⚠️ **Cross-staff XSS via `body_html` + `mark_safe` in preview.** Staff A can author a template with `<script>` in the body; staff B previews it and runs the script in their session (cookies, CSRF token, full admin access). Mitigate by sanitizing `body_html` through `bleach` *or* serving the preview from a sandboxed origin (e.g. `srcdoc` iframe with no shared cookies). Already noted in §1.6 and §7.
- `mailing.MailingLogAdmin` — ✅ **Read-only enforced.** All sensitive fields in `readonly_fields`; `has_add_permission` returns False. Search uses ORM `icontains` against `user__email` and `company_email_snapshot` — no SQL injection.
- `payments.CreditPackageAdmin` — ⚠️ **`list_editable = ("is_active", "order")` allows bulk inline edits.** Price/credit changes go through the regular form. ⚠️ **Mutating `price_eur` does NOT retroactively affect past purchases** because `StripePayment.amount_eur` and `credits_granted` are snapshotted on checkout creation — verified at `apps/payments/views.py:53-57`. ✅ But future Stripe sessions referencing the same `stripe_price_id` (if used) could go stale; current code uses dynamic pricing so this is moot.
- `payments.StripePaymentAdmin` — ✅ **Read-only enforced.** `has_add_permission=False` plus all fields in `readonly_fields`. Sensitive `stripe_payment_intent` only visible to staff (acceptable). Search by `stripe_session_id` is ORM-backed.
- `allauth.SocialAccount` + `SocialToken` admin (third-party) — 🔍 **Needs runtime verification** that token values are masked in the list view (allauth defaults to displaying token columns truncated, but worth confirming our installed version). Staff with `socialaccount.change_socialtoken` can in theory edit token values — should be restricted to superusers only.

### 1.6 Custom admin URLs (not auto-generated)

| URL | View | File | Check |
|---|---|---|---|
| `/admin/companies/company/import-xlsx/` | `CompanyAdmin.import_xlsx_view` | `apps/companies/admin.py:32` | File upload: xlsx formula injection (`=cmd\|...`), zip bomb, path traversal, size limit, CSRF, staff-only gate |
| `/admin/mailing/emailtemplate/<int:id>/preview/` | `EmailTemplateAdmin.preview_view` | `apps/mailing/admin.py` | `mark_safe` on rendered body — stored XSS via template body (staff can write HTML, but escalation risk via sessions) |

**Verdicts:**

- `/admin/companies/company/import-xlsx/` — ⚠️ **Several hardening items, no critical bugs.** (1) Staff-only gate confirmed via `self.admin_site.admin_view(self.import_xlsx_view)` at `apps/companies/admin.py:28` — the wrapper applies `staff_member_required`. (2) CSRF: inherits admin form-protected CSRF. ✅ (3) **xlsx formula / HTML injection:** if an imported row's `name` cell contains `<script>` or `=cmd|...`, the value is stored verbatim in `Company.name` and later renders into outbound emails via `{company_name}` placeholder substitution — **this lets a staff-controlled xlsx inject HTML into recipient inboxes.** Recipients are external companies, so blast radius is "deliverability + reputation hit," not direct user compromise. Mitigate by sanitizing imported strings (strip leading `=`, `+`, `-`, `@` per [OWASP CSV-injection guidance](https://owasp.org/www-community/attacks/CSV_Injection); HTML-escape on import). (4) **No file-size cap** beyond Django's default 2.5MB. (5) Zip-bomb / XXE: openpyxl 3.0+ uses defusedxml by default — ✅ verified. (6) Path traversal: file is read in-memory via `openpyxl.load_workbook(read_only=True)`, never written to disk. ✅
- `/admin/mailing/emailtemplate/<int:id>/preview/` — ⚠️ **Cross-staff stored XSS confirmed.** `mark_safe(body_html)` at `apps/mailing/admin.py` (preview_view) renders staff-authored HTML inline. Staff A authors `<img src=x onerror=fetch('/admin/users/1/?...')>`, staff B previews → script runs with B's session. Mitigations (any one): `bleach.clean()` on body before mark_safe, render in a sandboxed `<iframe srcdoc>`, or serve preview from a different cookie origin. ⚠️ **Secondary concern:** `EmailTemplate.render()` uses `str.format(**context)` — Python's `str.format` allows attribute walks like `{company_name.__class__}`, but since context values here are plain strings the worst leak is `<class 'str'>`. Not a critical vector, but `str.format_map(SafeDict(context))` would be cleaner.

---

## 2. Features / flows — end-to-end review

Each feature as a coherent attack path:

### 2.1 Authentication (OAuth Google + Microsoft)

- **Files:** `apps/accounts/adapters.py`, `apps/accounts/signals.py`, `config/settings.py` (SOCIALACCOUNT_PROVIDERS).
- **Checks:**
  - `is_open_for_signup` returns `True` unconditionally — email-based takeover scenarios.
    - **Verdict:** ⚠️ Confirmed unconditional in `apps/accounts/adapters.py:9`. See §1.2 cross-provider email-collision finding — this is the lever that makes email-collision exploitable. Acceptable for an open-signup product but document as a known posture.
  - `grant_signup_bonus` — double-grant possibilities, signal race conditions.
    - **Verdict:** ✅ Idempotency guarded by `if user.credits_remaining == 0` at `apps/accounts/signals.py:14`. Even if `user_signed_up` fires twice, the second grant is a no-op.
  - `pause_campaign_on_unlink` — correctness under concurrent unlink + tick.
    - **Verdict:** ✅ Guarded by `if user.is_campaign_active` (no-op when already paused). Concurrent Celery tick + unlink: worst case is a single in-flight send completes after pause — bounded, no compounding effect.
  - Scope downgrade: user logs in without `gmail.send` → sends fail silently.
    - **Verdict:** ⚠️ Confirmed. Allauth doesn't validate granted scopes at callback time. The engine raises a generic exception → `MailingLog.status=FAILED` per attempt, no user notification. Hardening: at callback, inspect `SocialToken.app.scope` vs. token grant and surface a dashboard banner if `gmail.send`/`Mail.Send` is missing.
  - Token storage: `SocialToken.token` / `token_secret` in plain text in DB.
  - Refresh token theft: if DB is compromised, attacker sends email as any user.
    - **Verdict:** ⚠️ Confirmed plain-text storage (allauth default). Mitigation: DB-level disk encryption (DigitalOcean Managed PostgreSQL has it on by default). For application-level encryption, replace `SocialToken` columns with `django-cryptography` `EncryptedCharField` — would require an allauth adapter override. Already documented as a known posture in `docs/features/security.md`.
  - Session fixation around `/accounts/login/`.
    - **Verdict:** ✅ Allauth rotates the session key on successful login (default Django behavior via `login()` → `request.session.cycle_key()`). No fixation vector observed.

### 2.2 CV management

- **Files:** `apps/accounts/models.py (CV)`, `apps/dashboard/views.py (upload_cv, set_active_cv, delete_cv)`, `apps/mailing/views.py (cv_download)`.
- **Checks:**
  - Upload: extension-only validation (`.pdf`), no content-type or magic-byte check.
    - **Verdict:** ⚠️ Confirmed. See §1.3 `upload_cv` finding — extension-only check; mitigated downstream by Spaces auto-detecting `Content-Type` from the file name suffix. Recommend adding a magic-byte check (first 4 bytes `%PDF`) before save.
  - Size limit: `10 * 1024 * 1024` enforced in Python; bypass via chunked transfer?
    - **Verdict:** ⚠️ The check happens in `upload_cv` *after* Django has read the body into memory. With `DATA_UPLOAD_MAX_MEMORY_SIZE` at default 2.5MB, requests over 2.5MB are streamed to a temp file, but the 10MB cap is the only ceiling — chunked uploads are subject to the same limit. Reinforce with `client_max_body_size 11M` in Nginx (deploy doc currently says 15M).
  - Filename: untrusted — confirm `FileField` + `upload_to="cvs/"` does not respect client-supplied paths.
    - **Verdict:** ✅ `FileSystemStorage` / `S3Boto3Storage` strip path components and reject traversal segments. Combined with `AWS_S3_FILE_OVERWRITE=False` (auto-suffixes collisions), there's no path-traversal vector.
  - IDOR on `set_active_cv` / `delete_cv` — `user=request.user` filter.
    - **Verdict:** ✅ Verified in §1.3. Both views use `get_object_or_404(CV, pk=cv_id, user=request.user)`.
  - `CV.delete()` overridden to remove the S3 object — verify it fires in all deletion paths (User cascade, management command, admin bulk delete).
    - **Verdict:** ⚠️ **Partial.** Fires in: per-row admin delete, `delete_account` view (explicit loop), `delete_user` management command (explicit loop). **Does NOT fire in:** Django admin bulk-delete action (`queryset.delete()`), or User cascade delete (DB-level `ON DELETE CASCADE`). Both paths leave orphaned objects in the Spaces bucket. Mitigation: register a `pre_delete` signal handler on `CV` that calls `instance.file.delete(save=False)`.
  - Pre-signed URL TTL (`AWS_QUERYSTRING_EXPIRE=300`) — leakage via Referer header, browser cache, email forwarding.
    - **Verdict:** ⚠️ TTL configured at 300s — fine. Referer leak: when the recipient clicks the `/cv/<uuid>/` link, the 302 redirect to Spaces sends `Referer: https://yourdomain.com/cv/<uuid>/` to Spaces. That's expected (Spaces doesn't egress further) and the Referer doesn't leave our trust boundary. Browser cache: see §1.1 verdict on `/cv/<uuid>/` — no `Cache-Control: no-store`.
  - Download endpoint rate limit (30/h/IP): brute-force token enumeration vs. UUID4 entropy.
    - **Verdict:** ✅ 30/h/IP * 122-bit UUID = guessing one valid token takes longer than the heat death of the sun. Sufficient.

### 2.3 Mailing engine (the main product surface)

- **Files:** `apps/mailing/tasks.py`, `apps/mailing/engine.py`.
- **Checks:**
  - `process_mailing_queue` runs as Celery worker — no request context, so any code that reads `request` here is a bug.
    - **Verdict:** ✅ Code does not reference `request` anywhere in `tasks.py` or `engine.py`. URL construction uses `settings.SITE_DOMAIN`, not `request.get_host()`.
  - Token refresh (`_refresh_google_token`, `_refresh_microsoft_token`): response parsing trust, error propagation, SSRF vector in the Bearer URL.
    - **Verdict:** ✅ Token endpoints are hardcoded HTTPS URLs (`https://oauth2.googleapis.com/token`, `https://login.microsoftonline.com/...`). No SSRF vector — the URL is not derived from the token or user data. Response parsing uses `resp.json()` and accesses `data["access_token"]` / `data.get("expires_in")` — `KeyError` on missing field would propagate (verified). ⚠️ `logger.error("Google token refresh failed: %s", resp.text)` at engine.py:51 logs the raw response body on failure — the body may contain `error_description` which can leak token-state hints. Already noted in §12.
  - `send_cv_email`: template rendering with `str.format` — **format string injection** if admin template values contain `{something_attr_access}`. Check whether `str.format_map` + a safe dict prevents `{user.__class__}` attribute access.
    - **Verdict:** ⚠️ Confirmed `str.format(**context)` at `apps/mailing/models.py:65-67`. Context is only `{company_name, cv_url, unsubscribe_url}` — all strings — so the worst attribute walk leaks `<class 'str'>`. Not directly exploitable, but still a brittle pattern. Recommend `str.format_map(SafeDict(context))` or jinja-style explicit substitution.
  - `scheme` selection based on `settings.DEBUG` — if DEBUG leaks into prod, `cv_url`/`unsubscribe_url` become `http://` and leak tokens.
    - **Verdict:** ⚠️ Confirmed at `apps/mailing/engine.py:139`, `apps/mailing/tasks.py:117`, `apps/payments/views.py:26,99`. Multiple sites couple `scheme` to `DEBUG`. If `DEBUG=True` ever ships to prod, every CV / unsubscribe / billing URL leaks the UUID over plaintext HTTP. Replace with explicit `SITE_SCHEME` env var (default `https`) — already noted in §6.
  - Email headers: `user.email` is put into `msg["From"]` — header injection if email contains CRLF.
    - **Verdict:** ✅ For `from_email`: Django's `validate_email` regex (used by `EmailField`) does not match CRLF, so `user.email` cannot contain header-injection chars. ⚠️ For `subject`: rendered from `EmailTemplate.subject` — staff-authored, no CRLF stripping. **A malicious staff member could inject `\r\nBcc: attacker@evil.com` into a template subject.** Python's `email.mime.MIMEMultipart["Subject"] = subject` does NOT raise on CRLF — relies on transport encoding. ⚠️ Recommend stripping `\r\n` from `subject` (and `body_html`) before passing to MIME.
  - MIME construction: `MIMEText(body_html, "html", "utf-8")` — HTML injection from admin-authored template (intentional but flag).
    - **Verdict:** ⏭️ **Out of scope for static review** — recipients (external companies) viewing HTML is the intended product behavior. Recipient-side XSS isn't our threat model since the email opens in the recipient's mail client, which has its own sandboxing.

### 2.4 Email templates

- **Files:** `apps/mailing/models.py (EmailTemplate.render)`, `apps/mailing/admin.py (preview_view)`, `apps/mailing/migrations/0002_seed_templates.py`.
- **Checks:**
  - `str.format` attack surface (see §2.3).
    - **Verdict:** ⚠️ See §2.3.
  - `body_html` is staff-authored — XSS not a concern for recipients (they're on different origins) but is for the admin preview.
    - **Verdict:** ⚠️ Confirmed cross-staff XSS surface. See §1.6.
  - Placeholder omissions → `KeyError` → `MailingLog.status=FAILED` but credit behavior.
    - **Verdict:** ✅ Verified at `apps/mailing/tasks.py:99-103` — generic `except Exception` clause catches `KeyError`, marks log FAILED, **does NOT decrement credits** (the `user.credits_remaining -= 1` only runs on the success path before the try). Credit-correctness preserved.
  - `mark_safe` in preview view.
    - **Verdict:** ⚠️ See §1.6.

### 2.5 Companies database

- **Files:** `apps/companies/models.py`, `apps/companies/importers.py`, `apps/companies/admin.py`.
- **Checks:**
  - Excel importer (`import_companies_from_xlsx`): openpyxl parses untrusted input. Zip bombs, XXE (openpyxl uses defusedxml by default — verify).
    - **Verdict:** ✅ openpyxl 3.0+ vendors defusedxml; XXE blocked. Zip-bomb: openpyxl reads with `read_only=True` which streams cells lazily, but the underlying zip is still extracted to memory. Bounded by Django upload limit. ⚠️ Pin a hard size cap.
  - `==`/formula injection in imported cells that later render in admin views or in sent emails (`{company_name}` is admin-controlled data but sourced from a user-uploaded file).
    - **Verdict:** ⚠️ Confirmed in §1.6. The CSV-injection class is mitigated only when admins re-export to xlsx (we don't have that today). The HTML-injection-into-email path is real today — recommend stripping leading `=`,`+`,`-`,`@` and HTML-escaping on import.
  - Header-row bypass: what if `email` column contains Python format syntax?
    - **Verdict:** ⚠️ The header is derived from row 1 via `str(h).strip().lower()` (apps/companies/importers.py:21). If a header contains `{...}`, it's stored only as a key in `header_map` and never `.format()`'d — safe. If a *cell value* in the `email` column contains `{user.__class__}`, it's stored as `Company.email`. Later `EmailTemplate.subject.format(company_name=...)` only uses `company.name`, not `company.email`, so no format-injection vector here.
  - Error-path information disclosure (we dump raw row errors to admin messages).
    - **Verdict:** ✅ Errors render messages like "Fila 5: email inválido 'foo'" via Django messages framework — auto-escaped HTML rendering. No XSS surface even with malicious cell values.

### 2.6 Blacklist & unsubscribe

- **Files:** `apps/companies/models.py (Blacklist)`, `apps/mailing/views.py (unsubscribe)`, `apps/mailing/tasks.py` (blacklist load).
- **Checks:**
  - `get_object_or_404` + `MailingLog.unsubscribe_token` — UUID lookup correct.
    - **Verdict:** ✅ Verified at `apps/mailing/views.py:62`. UUID lookup against unique-indexed field.
  - `Blacklist.objects.get_or_create(email=email, ...)` — race conditions.
    - **Verdict:** ✅ `unique=True` on `Blacklist.email` makes `get_or_create` atomic at the DB level (PostgreSQL handles the upsert). Concurrent clicks → at most one row inserted.
  - **State-changing GET:** unsubscribe uses GET so any email client / link prefetcher / antivirus scanner visiting the URL triggers the blacklist. Known deliverability risk — confirm it's intentional.
    - **Verdict:** ⚠️ See §1.1. Documented as intentional in `docs/features/blacklist-unsubscribe.md`.
  - Blacklist can only grow via this endpoint and admin. Verify: no accidental mass-insert path from other codepaths.
    - **Verdict:** ✅ `Blacklist.objects.create` / `get_or_create` only appears in `apps/mailing/views.py:67` and admin. No bulk-insert path.
  - Email enumeration via timing (does a non-existent token 404 at a different time than a valid one?).
    - **Verdict:** ⚠️ Theoretical timing diff exists (404 path is faster than the `get_or_create` + render path). Not exploitable without a valid token to start with — circular. Acceptable.

### 2.7 Credits

- **Files:** `apps/accounts/models.py (User.credits_remaining)`, `apps/accounts/signals.py`, `apps/mailing/tasks.py`, `apps/payments/views.py`.
- **Checks:**
  - Race conditions: concurrent Celery ticks could double-decrement. Is `-= 1` followed by `save(update_fields=["credits_remaining"])` atomic? **(Likely not — this is a classic lost-update bug.)**
    - **Verdict:** ❌ **Confirmed lost-update vulnerability.** `apps/mailing/tasks.py:84-85`: `user.credits_remaining -= 1; user.save(update_fields=["credits_remaining"])` is read-modify-write, not atomic. Two concurrent workers both reading credits=10 will both write credits=9 (one credit lost). In practice the slow-drip (5 min/user) makes this rare, but a concurrency-misconfigured worker (e.g. eventlet pool with multiple greenlets per user in a single tick) could trigger it. **Fix:** `User.objects.filter(pk=user.pk).update(credits_remaining=F('credits_remaining') - 1)`. Same pattern at `apps/payments/views.py:108-115` for credit additions.
  - Credit addition in webhook: same pattern, same risk.
    - **Verdict:** ❌ Same as above. Stripe sends webhooks rapidly under retries — duplicate webhook deliveries (already idempotent via status check), but if two distinct payments complete near-simultaneously, both `+= credits_granted` operations race.
  - Negative credits allowed? Admin can set to -1, engine query uses `__gt=0` so it simply skips — verify no signed-int overflow.
    - **Verdict:** ✅ `IntegerField` on PostgreSQL is `int4` (-2^31 to 2^31-1). Engine `__gt=0` filter excludes negative values cleanly. No overflow vector at realistic credit volumes.
  - Signup bonus race: what if `user_signed_up` fires twice?
    - **Verdict:** ✅ Guarded — see §2.1.

### 2.8 Payments (Stripe)

- **Files:** `apps/payments/views.py`, `apps/payments/models.py`.
- **Checks:**
  - `create_checkout`: `price_cents` computed from local `CreditPackage.price_eur` — can a user manipulate `package_id` to point at a cheaper pkg? (They can, but it's their own checkout — verify no coupling that would let them get more credits for less.)
    - **Verdict:** ✅ See §1.4. Price + credits both come from DB after `get_object_or_404`. No request-side override.
  - `success_url`/`cancel_url` — open redirect via `SITE_DOMAIN` spoofing (`Host` header override).
    - **Verdict:** ✅ Built from `settings.SITE_DOMAIN` (env-controlled), not `request.get_host()`. No `Host` header injection.
  - Webhook signature: `stripe.Webhook.construct_event` — verify constant-time comparison, check lib version for CVEs.
    - **Verdict:** ✅ Stripe SDK uses `hmac.compare_digest` internally. Library version 11.1.0 — pip-audit pending in §13.
  - Webhook idempotency: `payment.status == COMPLETED` early-return — race between two concurrent webhook deliveries.
    - **Verdict:** ⚠️ Idempotent guard at `apps/payments/views.py:98-99` reads-then-checks. Two simultaneous webhook deliveries for the same `stripe_session_id` could both pass the guard (read=PENDING, read=PENDING, both update). Stripe rarely fires duplicates within seconds, but `select_for_update()` inside a `transaction.atomic()` would close the window.
  - `stripe_customer_id` lookup by email — email change → cached ID points at the wrong customer.
    - **Verdict:** ⚠️ See §1.4. Cached ID stays correct across email changes (intentional). No exploit, just worth documenting.
  - Billing portal: `stripe.billing_portal.Session.create` — `return_url` built from `SITE_DOMAIN` (open redirect if host header trusted).
    - **Verdict:** ✅ Same as `success_url` — server-controlled.
  - PII in `StripePayment` audit trail after user deletion (`SET_NULL` preserves payment, not user email — verify).
    - **Verdict:** ✅ `StripePayment` has no `email` column; `user` FK is `SET_NULL`. After deletion, the row keeps `stripe_session_id`, `stripe_payment_intent`, `amount_eur`, `credits_granted`, timestamps. The actual email lives only in Stripe's records (out of our control). GDPR-compliant deletion preserves accounting without retaining PII on our side.

### 2.9 Dashboard

See §1.3 per-view checks. Additional whole-feature:

- `sent_today` / `sent_this_week` / `failed_count` — computed via Django ORM aggregates. No injection surface but confirm no raw SQL.
  - **Verdict:** ✅ Confirmed pure ORM (`apps/dashboard/views.py:30-35`). All `.filter().count()` calls — no `.raw()` / `.extra()` / `RawSQL`.
- `cvs = user.cvs.all()` — confirm the queryset is scoped to the current user (it is via `related_name="cvs"` + reverse FK).
  - **Verdict:** ✅ `user.cvs` is the reverse manager defined by `related_name="cvs"` on `CV.user` FK; cannot return another user's CVs.

### 2.10 Admin panel

- **File:** `apps/accounts/admin.py`, `apps/mailing/admin.py`, `apps/companies/admin.py`, `apps/payments/admin.py`.
- **Checks:**
  - Who is `is_staff`? Only `createsuperuser`-created accounts. Confirm social-login users can't self-promote.
    - **Verdict:** ✅ The OAuth signup flow goes through `DefaultSocialAccountAdapter.save_user`, which only sets `email`/`first_name`/`last_name` from the IdP. `is_staff` defaults to `False` on `AbstractUser` and is never assigned during signup. Self-promotion would require an existing staff session.
  - `/admin/` exposed publicly — recommend IP-restricting at the load balancer.
    - **Verdict:** ⚠️ Documented in `docs/features/admin-panel.md` and `docs/deploy.md` as "restrict at load balancer" — but not enforced in code. Brute-force on `/admin/login/` is theoretically possible (no rate limit on the admin login form). Mitigation: deploy-time IP allowlist, or add `django-axes` for failed-login throttling.
  - Admin session cookie separate from dashboard session? (It isn't — same session; confirm that's acceptable.)
    - **Verdict:** ⚠️ Same session — a user who is staff browses `/dashboard/` and `/admin/` with the same cookie. If a dashboard XSS exists (none found, but if), it'd inherit admin privileges. Hardening: split via `SESSION_COOKIE_PATH=/admin` for a separate admin cookie, or via subdomain.
  - Admin search fields — ORM injection is not possible via Django admin, but custom queries are.
    - **Verdict:** ✅ All registered ModelAdmins use `search_fields = ("...",)` which Django translates to ORM `Q(field__icontains=term)` — parameterized. No raw SQL anywhere.

### 2.11 Notifications (re-link emails)

- **File:** `apps/mailing/tasks.py (send_relink_notification)`.
- **Checks:**
  - `send_mail(..., fail_silently=True)` — SMTP errors swallowed. If SMTP creds are wrong, no user ever knows.
    - **Verdict:** ⚠️ Reliability concern, not a security one. A misconfigured `EMAIL_HOST_*` means re-link notifications never arrive — users see only a paused-campaign toggle. Mitigate by emitting a Sentry breadcrumb on send failure even when `fail_silently=True`.
  - `relink_url` built from `settings.SITE_DOMAIN` — host header injection → phishing URL.
    - **Verdict:** ✅ `SITE_DOMAIN` is env-driven, not derived from `request.get_host()`. Tasks have no `request` object anyway.
  - Content: `user.first_name or user.email` — XSS if rendered in an HTML-aware client (body is plain text — verify).
    - **Verdict:** ✅ Plain-text email (`send_mail` with no `html_message` arg). Even if rendered as HTML by a permissive client, `\n\n` joins prevent inline script execution.

### 2.12 Health check

- **File:** `config/health.py`.
- **Checks:**
  - Public unauthenticated endpoint — DoS amplification via unlimited polling (no rate limit currently).
    - **Verdict:** ⚠️ See §1.1.
  - Response content: `{"status":"ok","db":true,"cache":true}` — no sensitive info, good.
    - **Verdict:** ✅ No version/build/env info disclosure.
  - DB query: `SELECT 1` — no injection.
    - **Verdict:** ✅ Hardcoded literal. No injection surface.
  - Cache write: `cache.set("healthz:ping", "ok", timeout=5)` — minor key-collision risk with another `healthz:ping` in the namespace.
    - **Verdict:** ✅ The key is application-internal; only set/read by `healthz`. No collision in practice.

---

## 3. Middleware & request/response chain

- **Files:** `config/settings.py (MIDDLEWARE)`, `apps/mailing/middleware.py`.
- **Checks:**
  - Order matters: `WhiteNoiseMiddleware` → `SessionMiddleware` → `CsrfViewMiddleware` → `AuthenticationMiddleware` → `AccountMiddleware` → `RatelimitMiddleware`. Verify order.
    - **Verdict:** ✅ Verified at `config/settings.py:34-45`. `SecurityMiddleware` first, `WhiteNoiseMiddleware` second, then `Session → Common → CSRF → Auth → Messages → Clickjacking → Account → Ratelimit`. Standard recommended order; no inversions.
  - `RatelimitMiddleware.process_exception`: 429 response content is static — no user input reflected.
    - **Verdict:** ✅ Static `"Demasiadas peticiones. Intenta de nuevo más tarde."` plaintext body. No reflection.
  - `django.middleware.security.SecurityMiddleware` — rely on `SECURE_*` settings (see §6).
    - **Verdict:** ✅ Enabled. Behavior gated on `SECURE_SSL_REDIRECT`, `SECURE_HSTS_*`, `SECURE_CONTENT_TYPE_NOSNIFF`, `SECURE_REFERRER_POLICY` — all configured. See §6 for env-gating concerns.
  - `XFrameOptionsMiddleware` — `X_FRAME_OPTIONS="DENY"` hardcoded.
    - **Verdict:** ✅ Hardcoded to `DENY` at `config/settings.py:267`. Clickjacking blocked.

---

## 4. Models — data integrity & DB-level concerns

Every model to review for field types, constraints, `on_delete` semantics, and indexes.

| Model | File | Check |
|---|---|---|
| `accounts.User` | `apps/accounts/models.py` | Custom fields' defaults; `active_cv` FK `SET_NULL`; `stripe_customer_id` indexed + blank-default |
| `accounts.CV` | `apps/accounts/models.py` | `CASCADE` to User (correct); overridden `delete()` fires in all paths? |
| `companies.Company` | `apps/companies/models.py` | `email` unique; `SET_NULL` on FK from MailingLog |
| `companies.Blacklist` | `apps/companies/models.py` | Email unique; no FK relationships |
| `mailing.EmailTemplate` | `apps/mailing/models.py` | `body_html` TextField — size bounds |
| `mailing.MailingLog` | `apps/mailing/models.py` | UUID tokens unique + indexed; `cv` FK `SET_NULL`; `company_email_snapshot` for GDPR |
| `mailing.SystemSettings` | `apps/mailing/models.py` | Singleton via `save(pk=1)` — race condition? |
| `payments.CreditPackage` | `apps/payments/models.py` | Nothing sensitive — check price decimal precision |
| `payments.StripePayment` | `apps/payments/models.py` | `stripe_session_id` unique; user `SET_NULL` preserves audit |

**Verdicts:**

- `accounts.User` — ✅ Custom field defaults sound (`credits_remaining=0`, `is_campaign_active=False`). `active_cv` FK `SET_NULL` correct (deleted CV row shouldn't cascade to delete the user). `stripe_customer_id` indexed, blank-default — confirmed at migration `0002_cv_model_and_customer.py`.
- `accounts.CV` — ⚠️ See §2.2 — `delete()` override doesn't fire on User-cascade or admin bulk delete. Functional `CASCADE` to User correct; orphaned-S3-object risk on the two unhooked paths.
- `companies.Company` — ✅ `email = EmailField(unique=True)` enforces uniqueness via DB constraint. FK from `MailingLog` is `SET_NULL` — confirmed.
- `companies.Blacklist` — ✅ `email = EmailField(unique=True)` makes `get_or_create` race-free.
- `mailing.EmailTemplate` — ⚠️ `body_html = TextField()` has **no max length** in the DB or model. PostgreSQL `text` is up to 1GB, so a malicious staff member could insert a multi-MB HTML body that's then included in every send (huge bandwidth + spam-filter trigger). Add `max_length=50000` or model-level validation.
- `mailing.MailingLog` — ✅ Both UUID tokens are `unique=True, db_index=True`. `cv` FK `SET_NULL`. `company_email_snapshot` populated on save — preserves audit through `Company` deletion.
- `mailing.SystemSettings` — ✅ Singleton enforced via `save(self, *args, **kwargs): self.pk = 1; super().save(...)` — concurrent inserts collide on PK. `delete()` is a no-op. ⚠️ **Edge case:** `get_or_create(pk=1)` is the read path — under high concurrency, two callers may race on initial insert. PostgreSQL handles via `ON CONFLICT` if `get_or_create` is wrapped — verified Django uses SAVEPOINT. ✅
- `payments.CreditPackage` — ✅ `price_eur = DecimalField(max_digits=8, decimal_places=2)` — sufficient precision for cents.
- `payments.StripePayment` — ✅ `stripe_session_id` unique. User `SET_NULL` preserves audit. No PII columns.

**ORM-level:**
- Every `.filter()` and `.get()` call: confirm no `**request.GET` unpacking (none found).
  - **Verdict:** ✅ `grep -rn "\*\*request\." apps/` returns nothing. No mass-assignment vector.
- Every `.raw()` / `.extra()` / `RawSQL`: search the codebase (none expected).
  - **Verdict:** ✅ `grep -rn "\.raw(\|\.extra(\|RawSQL\|cursor.execute" apps/ config/` returns only `config/health.py:14` (`cursor.execute("SELECT 1")`, hardcoded literal). No injection vector.
- `select_related` / `prefetch_related` usage (performance, not security).
  - **Verdict:** ⏭️ Out of scope for security review.

---

## 5. Celery tasks (async code paths)

- **Files:** `apps/mailing/tasks.py`, `config/celery.py`.
- **Checks:**
  - `process_mailing_queue` runs without a request. Confirm no code inside reads `request`.
    - **Verdict:** ✅ Verified in §2.3. Task uses `settings.SITE_DOMAIN` and `settings.DEBUG` only.
  - `send_relink_notification(user_pk)` — task argument is a primary key, not an object (good). Logged in plain text via Celery result backend if it stays in Redis — PII in `user_pk`? No, just an int.
    - **Verdict:** ✅ Argument is `user_pk` (int). No PII serialized into the broker. Celery's default JSON serializer doesn't pickle, so no deserialization RCE vector.
  - `CELERY_BROKER_URL` = Redis — ensure Redis itself is auth'd (AUTH + network-restricted).
    - **Verdict:** ⚠️ `docker-compose.yml` exposes Redis on `6379:6379` to host (line 19-20) **without** an `AUTH` password configured (`config/settings.py:165` uses bare `redis://localhost:6379/0`). For local dev this is fine; for prod, `REDIS_URL` must include credentials and Redis must be network-restricted. Document explicitly in `docs/deploy.md` (currently absent).
  - Task serialization (`json` by default) — no pickle.
    - **Verdict:** ✅ Celery 5.x defaults to JSON (`task_serializer`, `accept_content`). No `CELERY_ACCEPT_CONTENT=['pickle']` override observed in settings.
  - `autodiscover_tasks()` — only picks up `apps/*/tasks.py`; verify no stray task in surprising places.
    - **Verdict:** ✅ `find apps -name "tasks.py"` returns only `apps/mailing/tasks.py`. No stray `@shared_task` decorators elsewhere.

---

## 6. Settings / configuration

- **File:** `config/settings.py`.
- **Checks:**
  - `DEBUG` default is `False` — but `SITE_DOMAIN=localhost:8000` default means a misconfigured prod could use `http://` links.
    - **Verdict:** ⚠️ See §2.3. `DEBUG=True` in prod compounds two issues: scheme downgrade in URLs + Django's debug error pages disclose tracebacks. Both are operator errors but the cost is high; consider an explicit `SITE_SCHEME` env var + a `manage.py check --deploy` step in CI that fails on `DEBUG=True`.
  - `SECRET_KEY` has an insecure default — verify it's overridden in every environment.
    - **Verdict:** ⚠️ Default `"django-insecure-changeme-in-production"` at `config/settings.py:6`. Django will warn via `manage.py check --deploy`. Doesn't fail-closed. Recommend raising at startup if the default value is detected and `DEBUG=False`.
  - `ALLOWED_HOSTS` defaults to `localhost,127.0.0.1`. If `ALLOWED_HOSTS=*` ever sets, host header injection opens up.
    - **Verdict:** ⚠️ Default is safe. Operator must explicitly set `ALLOWED_HOSTS=*` to break this — document a "never use `*`" guideline (already in `docs/deploy.md`).
  - `CSRF_TRUSTED_ORIGINS` — comma-separated, confirm every entry is `https://`.
    - **Verdict:** ⚠️ Defaults to empty `""`. Operator-set per environment. Document that entries must include scheme (Django 4+ requires this) — already correct in `.env.example`.
  - `SECURE_PROXY_SSL_HEADER` only set when `TRUST_PROXY_SSL_HEADER=True` — if set behind a proxy that doesn't strip `X-Forwarded-Proto`, clients can force `https` detection.
    - **Verdict:** ⚠️ Only set when explicitly opted in via env (`config/settings.py:271-272`). The proxy must strip incoming `X-Forwarded-Proto` from clients. Documented in `docs/deploy.md`. ✅ Implementation correct.
  - `IGNORE_EXCEPTIONS=True` on cache: rate limiting silently off when Redis is down.
    - **Verdict:** ⚠️ Confirmed at `config/settings.py:196`. Trade-off is intentional (availability over security), but means an attacker can DoS Redis to disable rate limiting. Hardening: monitor Redis uptime, alert on cache exceptions.
  - `SOCIALACCOUNT_LOGIN_ON_GET=True` — CSRF on social login initiation (known allauth behavior; confirm acceptable).
    - **Verdict:** ⚠️ See §1.2. Known allauth behavior; mitigated by OAuth state nonce.
  - `ACCOUNT_AUTHENTICATION_METHOD = "email"` with `ACCOUNT_USERNAME_REQUIRED = False` — email-based identity, verify uniqueness constraint on User.email (it's `blank=True` in `AbstractUser` by default).
    - **Verdict:** ❌ **`User.email` is NOT unique by default.** `AbstractUser.email` is `EmailField(blank=True)` without `unique=True`. Two users could in theory have the same email if allauth's adapter doesn't enforce it. Allauth does enforce email uniqueness via `EmailAddress` table (when `ACCOUNT_EMAIL_VERIFICATION` is enabled), but with `ACCOUNT_EMAIL_VERIFICATION="none"`, the enforcement weakens. 🔍 **Needs runtime test:** create two SocialAccounts with the same email via separate providers — does allauth merge or duplicate? If duplicate, login is ambiguous.
  - `AWS_DEFAULT_ACL = "private"` — if ever flipped to `public-read`, every CV is exposed.
    - **Verdict:** ✅ Hardcoded to `"private"` at `config/settings.py:157`. No env-override knob. ✅
  - `AWS_S3_FILE_OVERWRITE = False` — prevents filename collisions.
    - **Verdict:** ✅ Hardcoded at `config/settings.py:158`.
  - Sentry `send_default_pii=False` — confirm.
    - **Verdict:** ✅ Hardcoded at `config/settings.py:252`. PII-free transport to Sentry.
  - `SESSION_ENGINE` not explicitly set → defaults to DB-backed sessions (acceptable).
    - **Verdict:** ✅ DB-backed sessions are revocable (delete row to invalidate). Acceptable.

---

## 7. Templates — XSS and SSRF surfaces

For each template, verify auto-escape is on (Django default) and identify `|safe` / `mark_safe` / `autoescape off` usage.

| Template | File | Check |
|---|---|---|
| `base.html` | `templates/base.html` | Base layout — CSP meta, CDN integrity for Tailwind |
| `home.html` | `templates/home.html` | Fully static — low risk |
| `account/login.html` | `templates/account/login.html` | Error messages rendered from allauth — verify no unescaped strings |
| `dashboard/index.html` | `templates/dashboard/index.html` | Renders `user.email`, `cv.name`, `log.company_email_snapshot`, `log.email_template.name` — all user/admin input |
| `dashboard/delete_account.html` | `templates/dashboard/delete_account.html` | Renders `user.email` — low risk |
| `mailing/cv_not_found.html` | `templates/mailing/cv_not_found.html` | Static |
| `mailing/unsubscribe.html` | `templates/mailing/unsubscribe.html` | Renders `email` from `company_email_snapshot` — ensure auto-escape |
| `payments/packages.html` | `templates/payments/packages.html` | Renders `CreditPackage.description` — admin-authored, low risk but confirm |
| `payments/success.html` | `templates/payments/success.html` | Static / payment info |
| `admin/companies/import_xlsx.html` | `templates/admin/companies/import_xlsx.html` | Staff-only upload form — CSRF token |
| `admin/companies/company/change_list.html` | `templates/admin/companies/company/change_list.html` | Import button injection |
| `admin/mailing/emailtemplate/preview.html` | `templates/admin/mailing/emailtemplate/preview.html` | **`{{ body_html }}` is `mark_safe`** — staff-authored HTML renders as-is. Confirm staff-only access. |

**Verdicts:**

- `base.html` — ⚠️ **Tailwind CDN loaded without SRI:** `<script src="https://cdn.tailwindcss.com"></script>` at `templates/base.html:7` has no `integrity=`/`crossorigin=` attributes. If `cdn.tailwindcss.com` is compromised or DNS-hijacked, every page on the site executes attacker JS. No CSP `meta` header either. Mitigations: self-host Tailwind via `whitenoise`, or add SRI + CSP `script-src 'self' cdn.tailwindcss.com 'sha384-...'`.
- `home.html` — ✅ Static. Only `{% now "Y" %}` from base; no user input.
- `account/login.html` — ✅ Allauth-error rendering uses default auto-escape; no `|safe` filters in this file.
- `dashboard/index.html` — ✅ All user-controlled fields (`{{ user.email }}`, `{{ cv.name }}`, `{{ user.area_filter }}`, `{{ log.company_email_snapshot }}`, `{{ log.email_template.name }}`) render under default auto-escape. No `|safe` / `mark_safe` usage.
- `dashboard/delete_account.html` — ✅ Renders only `{{ user.email }}`, auto-escaped.
- `mailing/cv_not_found.html` — ✅ Fully static.
- `mailing/unsubscribe.html` — ✅ `{{ email }}` (the recipient's email from `MailingLog.company_email_snapshot`) rendered with auto-escape; even a maliciously-named company can't XSS this page.
- `payments/packages.html` — ✅ `{{ package.name }}`, `{{ package.description }}`, `{{ package.price_eur }}`, `{{ package.credits }}` all auto-escaped. Admin-authored content + auto-escape = safe.
- `payments/success.html` — ✅ `{{ payment.credits_granted }}` is an integer; no HTML risk.
- `admin/companies/import_xlsx.html` — ✅ `{% csrf_token %}` present, error rendering auto-escaped.
- `admin/companies/company/change_list.html` — ✅ Just adds an `<a>` button, no dynamic content.
- `admin/mailing/emailtemplate/preview.html` — ⚠️ See §1.6 — confirmed `mark_safe(body_html)` rendering. Cross-staff XSS surface.

**Cross-template grep verification:** `grep -rn "|safe\|mark_safe\|autoescape off"` returns only `apps/mailing/admin.py:76` (the preview view's `mark_safe(body_html)`). No template-side `|safe` filters or `{% autoescape off %}` blocks anywhere.

---

## 8. External integrations

### 8.1 Google Gmail API

- **File:** `apps/mailing/engine.py:91` (`_send_via_gmail`).
- **Checks:**
  - URL hardcoded — no SSRF.
    - **Verdict:** ✅ `https://gmail.googleapis.com/gmail/v1/users/me/messages/send` — literal.
  - Bearer token — log scrubbing of tokens on error.
    - **Verdict:** ⚠️ `raise Exception(f"Gmail API error {resp.status_code}: {resp.text}")` at engine.py:108 — `resp.text` doesn't contain the bearer token (Google echoes only error info), but if Sentry captures the exception, the response body lands in Sentry. Acceptable; PII flag is `send_default_pii=False` so the token wouldn't be redacted automatically. Worth confirming during runtime test.
  - Response validation: only `status_code in (200, 202)`.
    - **Verdict:** ✅ Strict allow-list. Anything else raises.
  - MIME assembly — header injection via `from_email` (user's email) or `to_email` (company email).
    - **Verdict:** See §2.3. `user.email` validated by Django; `company.email` validated by `EmailField` on Company. ⚠️ `subject` is the unprotected vector.
  - Timeout: 15s — DoS amplification via slow Gmail (unlikely).
    - **Verdict:** ✅ Bounded. A single send caps the worker for at most 15s.

### 8.2 Microsoft Graph API

- **File:** `apps/mailing/engine.py:111` (`_send_via_microsoft`).
- Same checks as §8.1, plus: `saveToSentItems: False` — verify it's still being honored.
  - **Verdict:** ✅ `saveToSentItems: False` set at `apps/mailing/engine.py:124`. Microsoft Graph API documents this as a respected flag. Confirmed at static level; runtime verification could check the user's Outlook "Sent" folder after a test send.

### 8.3 Google / Microsoft OAuth token endpoints

- **File:** `apps/mailing/engine.py:32`, `:61`.
- **Checks:**
  - Refresh-token value placed in POST body — TLS enforced by URL (hardcoded `https://`).
    - **Verdict:** ✅ Both URLs hardcoded `https://`.
  - Client secret in body — not logged.
    - **Verdict:** ⚠️ `requests.post(..., data={"client_secret": ..., "refresh_token": ...})` — by default `requests` doesn't log bodies, but if `urllib3` is configured to log at DEBUG, the request body could leak. Verify production `LOG_LEVEL=INFO` (current default). ✅ Default config safe.
  - `timeout=10` — verify.
    - **Verdict:** ✅ Confirmed at engine.py:47 and engine.py:77.

### 8.4 Stripe API

- **File:** `apps/payments/views.py`.
- **Checks:**
  - `stripe.api_key = settings.STRIPE_SECRET_KEY` — set at module import; if `settings` is reloaded it won't update.
    - **Verdict:** ⚠️ Module-level assignment at `apps/payments/views.py:12`. Settings reload (rare) wouldn't propagate. Acceptable for production where settings don't change at runtime.
  - `stripe.Webhook.construct_event` — library version pinned (11.1.0) — check CVEs.
    - **Verdict:** 🔍 Pending §13 dependency scan. Stripe SDK is generally well-maintained; known constant-time HMAC.
  - `stripe.Customer.list(email=...)` — verify `limit=1` and handle paginated results.
    - **Verdict:** ✅ `limit=1` set explicitly; `customers.data[0]` only accessed after `if not customers.data` guard. No pagination needed.

### 8.5 DigitalOcean Spaces (boto3)

- **File:** `apps/mailing/views.py:32`, `config/settings.py` (storage backend).
- **Checks:**
  - IAM key scope — bucket-restricted.
  - `signature_version="s3v4"` — correct for Spaces.
  - Pre-signed URL TTL respected.
  - `AWS_S3_ENDPOINT_URL` — SSRF if attacker-controlled (it's from env, safe).
    - **Verdict:** ⚠️ **IAM key scope is operational, not visible in code.** Documented in `docs/features/security.md` as "scope to a single bucket" — operator responsibility. ✅ `signature_version="s3v4"` confirmed at `apps/mailing/views.py:41`. ✅ TTL `AWS_QUERYSTRING_EXPIRE=300` honored. ✅ Endpoint from env (operator-controlled), not request — no SSRF.

### 8.6 SMTP (system notifications)

- **File:** `apps/mailing/tasks.py (send_relink_notification)`.
- **Checks:**
  - `EMAIL_HOST_PASSWORD` at rest in `.env`.
    - **Verdict:** ✅ Sourced from `.env` via `python-decouple`; never logged. `.gitignore` excludes `.env`.
  - TLS enforced (`EMAIL_USE_TLS=True` default).
    - **Verdict:** ✅ `EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)` at `config/settings.py:180`.
  - From-header spoofing prevention.
    - **Verdict:** ✅ `from_email=settings.DEFAULT_FROM_EMAIL` is server-controlled. Recipient SMTP servers will validate via SPF/DKIM/DMARC against the configured domain — operator responsibility.

---

## 9. Management commands (CLI surfaces)

| Command | File | Check |
|---|---|---|
| `setup_periodic_tasks` | `apps/mailing/management/commands/setup_periodic_tasks.py` | Idempotency, no shell injection |
| `delete_user` | `apps/accounts/management/commands/delete_user.py` | `--email` arg validation; `--yes` bypass of interactive prompt; ensure cascade is complete; logs destination (stdout only) |
| Standard Django `createsuperuser`, `migrate`, `collectstatic` | built-in | Command-line only; verify not exposed via HTTP |

---

## 10. Rate limiting & DoS

- **File:** `apps/mailing/views.py` (`@ratelimit` decorators), `config/settings.py (RATELIMIT_ENABLE)`.
- **Checks:**
  - Current coverage: `/cv/<uuid>/` 30/h/IP; `/unsubscribe/<uuid>/` 10/h/IP.
  - **Uncovered endpoints:** `/healthz`, `/accounts/*`, `/dashboard/*`, `/payments/*`, `/admin/*`, `/payments/webhook/`.
  - `IGNORE_EXCEPTIONS=True` → rate limit silently off when Redis is down.
  - Rate-limit key is `ip` — trivially bypassed via IP rotation; consider `(ip, user_agent)` or session-based for authenticated endpoints.
  - Large file uploads: no nginx-level limit shown (`client_max_body_size 15M` is suggested in deploy docs but not enforced in Django).

---

## 11. Secrets management

- **Files:** `.env` (local), `.env.example` (template), `config/settings.py` (via `python-decouple`).
- **Checks:**
  - `.gitignore` excludes `.env` (verified).
  - Every `config("X")` call has a safe default or is required at startup.
  - Nothing in code falls back to an insecure value in `DEBUG=True` mode.
  - OAuth client secrets, Stripe keys, AWS creds, SMTP passwords — all through env.
  - Celery broker URL (`REDIS_URL`) may contain credentials — verify not logged.
  - Sentry DSN — itself an auth token, should not appear in client-side code.

---

## 12. Logging — PII exposure

- **File:** `config/settings.py (LOGGING)`, logger calls throughout `apps/`.
- **Checks:**
  - `logger.info("Sent CV: user=%s → company=%s", user.email, company.email)` — emails in logs (PII under GDPR).
  - `logger.warning("No eligible companies for user %s", user.email)` — same.
  - Sentry `send_default_pii=False` — confirms emails not sent to Sentry.
  - Celery task args logged by default — `send_relink_notification(user_pk=123)` is fine.
  - OAuth tokens: `_refresh_google_token` logs `resp.text` on failure — error response may contain refresh token hints.

---

## 13. Dependencies / supply chain

- **File:** `requirements.txt`.
- **Checks (run `pip-audit` or similar):**
  - Django 4.2.16 — check for CVEs beyond this version.
  - allauth 0.63.6, django-storages 1.14.4, celery 5.4.0, stripe 11.1.0, boto3 1.35.36, openpyxl 3.1.5, Pillow 10.4.0, requests 2.32.3, cryptography 43.0.3, PyJWT 2.9.0.
  - Transitive dependencies not pinned.
  - Flower 2.0.1 recently added — check CVE list.
  - No `pip install` from git URLs.

---

## 14. Deployment / infrastructure

- **Files:** `docker-compose.yml`, `Dockerfile`, `scripts/backup_db.sh`, `docs/deploy.md`.
- **Checks:**
  - Dockerfile: runs as root (`WORKDIR /app`, no `USER` directive). Recommend non-root.
  - `docker-compose.yml`: DB/Redis ports exposed to host (`5432:5432`, `6379:6379`) in local dev — should not happen in prod config.
  - Flower exposed on `127.0.0.1:5555` (good) — reverse-proxy auth layer (Nginx + Basic Auth) documented but not enforced.
  - `FLOWER_BASIC_AUTH=admin:changeme` default — confirm it's rotated in deployment.
  - `scripts/backup_db.sh`: uses `PGPASSWORD` env var — visible in `ps aux` on multi-tenant hosts.
  - Backup destination bucket lifecycle retention configured externally.
  - TLS termination (`SECURE_PROXY_SSL_HEADER`) trust assumption.

---

## 15. Data privacy / GDPR

- **Files:** `apps/accounts/management/commands/delete_user.py`, `apps/dashboard/views.py (delete_account)`.
- **Checks:**
  - User-initiated deletion: session invalidated, all CVs deleted from Spaces, `User.delete()` cascades.
  - `StripePayment.user = SET_NULL` — audit trail survives; email NOT retained on the payment row (confirm).
  - `MailingLog.company_email_snapshot` — recipient's email is preserved for audit. Is this a GDPR issue for the recipient (a data subject who didn't consent)?
  - `Blacklist.email` — subject's email kept indefinitely. Arguably lawful interest, but document the retention policy.
  - Admin-initiated `delete_user --yes` bypasses the confirmation — log trail? Currently only stdout.
  - Data export endpoint: **missing** (GDPR Article 20 — right to portability). Flag as open gap.

---

## 16. CSRF posture

- **Protected by default** on all `POST` except `@csrf_exempt`:
  - `/payments/webhook/` — signature-verified.
- **State-changing GETs (anti-pattern):**
  - `/unsubscribe/<uuid>/` — GET triggers blacklist insert. Flag: email-client link prefetch can trigger.
  - `/accounts/social/login/...` — allauth GET-starts OAuth; mitigated by state param.
- **CSRF token missing from forms?** Every `<form>` in every template must have `{% csrf_token %}` for POST — audit each.

---

## 17. Session / cookie handling

- **File:** `config/settings.py`.
- **Checks:**
  - `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` — env-gated, must be `True` in prod.
  - `SESSION_COOKIE_HTTPONLY` — default True in Django (confirm not overridden).
  - `SESSION_COOKIE_SAMESITE` — default `Lax` (confirm).
  - Session expiry: Django default is 2 weeks — consider shorter for a product that auto-sends email.
  - Logout invalidates session: verify `delete_account` calls `logout()` before `user.delete()` (it does — `apps/dashboard/views.py`).

---

## 18. Testing — what's NOT yet covered

- OAuth end-to-end flow (Google's IdP mocked only at the engine layer).
- CSRF token presence in templates (no assertion).
- Rate-limit behavior under multi-IP attack (single-IP only).
- File-upload polyglots / zip bombs / formula injection in xlsx.
- Admin preview XSS (staff-authored HTML).
- Stripe webhook under replay / malformed payload stress.
- Celery task race conditions (concurrent decrement).

---

## Summary — count of surfaces to check

| Category | Count |
|---|---|
| Public URL routes | 5 |
| Allauth routes | ~11 (third-party) |
| Authenticated dashboard routes | 7 |
| Authenticated payment routes | 4 |
| Custom admin URLs | 2 |
| Django admin registrations | 10 |
| Models | 9 |
| Celery tasks | 2 |
| Management commands | 2 (custom) + built-ins |
| Templates | 13 |
| External integrations | 6 |
| Middleware | 1 custom + 9 standard |

Total direct review items: **~80** distinct code/config surfaces.

---

## How to use this document

1. Testers pick a category, work top-to-bottom.
2. For each item, annotate with ✅ / ⚠️ / ❌ and line-level notes.
3. Consolidate findings into a single report at the end — do not edit this file during testing; it's the checklist, not the findings.
4. Cross-reference each item against the relevant feature doc in `docs/features/` for intended behavior.
