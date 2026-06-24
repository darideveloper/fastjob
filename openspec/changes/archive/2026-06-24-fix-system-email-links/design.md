## Context

Today, system emails embed absolute URLs built with `f"{settings.SITE_SCHEME}://{settings.SITE_DOMAIN}/path"` in seven different call sites (`apps/accounts/tasks.py:18,19,48,80`, `apps/payments/tasks.py:21,22`, `apps/mailing/tasks.py:285`, and `apps/mailing/engine.py:374-375`). Paths are hard-coded strings, never reverse-resolved. One of them — the `billing_url` in the payment receipt — drifted from the real route and now 404s for every paying customer. The same class of bug can reappear whenever a route is renamed. The `unsubscribe_url` in the campaign engine (`engine.py:374-375`) is currently correct but uses the same fragile pattern and feeds BOTH the `{unsubscribe_url}` placeholder in the body AND the `List-Unsubscribe` / `List-Unsubscribe-Post` MIME headers — a silent break there would corrupt every campaign email's unsubscribe flow. A second latent issue: `apps/payments/views.py:billing_portal` is decorated with `@require_POST`, so even if the link pointed at the right path, an email click (a GET) would still 405. A third: the welcome context carries an unused `oauth_url` variable. A fourth: `SystemSettings.email_footer_text` is rendered `|safe` with no validation, so an admin typo or stale link ships to every recipient. A fifth: `campaign_paused_notification` tells the user "revisa tu dashboard" but provides no clickable link.

The change has two distinct surfaces — a one-line fix plus a set of defensive guardrails — and needs to leave the existing test suite green while adding new tests that fail if a future rename breaks an email link.

## Goals / Non-Goals

**Goals:**
- Stop the production 404 on the payment-receipt billing link.
- Make the billing portal reachable by a single GET from an email client.
- Centralize absolute-URL construction in one helper so renames can't drift.
- Add automated coverage that asserts every URL embedded in a system email resolves to a registered route.
- Validate admin-entered footer HTML for safe `href` schemes.
- Remove dead code (`oauth_url` welcome context).
- Add a clickable dashboard link to `campaign_paused_notification` (missing link, not broken).

**Non-Goals:**
- Renaming the billing-portal route slug (`portal` → `billing`) — left as a follow-up; the helper makes such a rename safe.
- Touching the user-authored `EmailTemplate.body_html` content (the HTML a staff user types, including `{cv_url}`/`{unsubscribe_url}` placeholders) — that is free-form content, not a system-built URL. The system-built `unsubscribe_url` VALUE injected by `engine.py` IS in scope.
- Stripe success/cancel/return URLs in `apps/payments/views.py:35,107` — not email links; follow-up candidate for the same `abs_url()` helper.
- Changing the email template structure or copy beyond what's needed to wire the helper and the new dashboard link.
- Adding a system check framework for arbitrary URL fragments in templates (considered, deferred — covered by the test harness).

## Decisions

### D1. Fix the path string, not the route slug

The receipt email says `/payments/billing/`. Two options:
- **(a) Edit `apps/payments/tasks.py:22` to `/payments/portal/`.** One-line diff. URL stays as-is.
- **(b) Rename the route to `payments/billing/` in `apps/payments/urls.py`.** Larger blast radius — affects the only existing call site and any external bookmark; also the literal string `/payments/portal/` is referenced in tests.

Pick (a). Smallest diff, lowest risk, the helper introduced below makes a future rename trivial.

### D2. Drop `@require_POST` from `billing_portal`; keep `@login_required`

`billing_portal` is only stateful in that it calls `stripe.billing_portal.Session.create()` and then `return redirect(session.url)`. That work is safe to do on a GET: the Stripe call is idempotent and returns a fresh session URL, and `@login_required` already protects unauthenticated access. The current `@require_POST` was almost certainly a misapplied copy of `stripe_webhook`'s decorator. Drop it. No existing call site depends on POST semantics — the only invoker was meant to be the email link.

### D3. `abs_url(viewname, *args, **kwargs)` helper in `apps/core/urls.py`

```python
from django.urls import reverse
from django.conf import settings

def abs_url(viewname, *args, **kwargs):
    return f"{settings.SITE_SCHEME}://{settings.SITE_DOMAIN}{reverse(viewname, args=args, kwargs=kwargs)}"
```

- Thin wrapper around `reverse()` plus the site prefix. Returns a fully qualified URL.
- Single source of truth for `SITE_SCHEME` + `SITE_DOMAIN` concatenation. All seven email-URL call sites migrate to it (the six task sites plus `apps/mailing/engine.py:374-375` for the campaign `unsubscribe_url`).
- Reject `viewname` values that are not registered names — `reverse()` raises `NoReverseMatch`, which surfaces in tests immediately.
- Lives next to other cross-cutting concerns in `apps/core/`.

**Alternatives considered:**
- *A custom template tag* (`{% abs_url 'dashboard' %}`) — more idiomatic in templates, but the URLs are built in Python tasks, not in templates, so a Python helper is the right shape.
- *A DRF-style `request.build_absolute_uri(reverse(...))`* — would need the request object threaded through Celery tasks; not viable.
- *A site-URL Django setting (`ABSOLUTE_URL_PREFIX`)* combined with `{% url %}` in templates — would still leave the Python tasks with literal paths, only moves the problem.

**Why include `engine.py:unsubscribe_url`:** the `unsubscribe_url` value is system-built (not user-authored — only the template BODY is user-authored). It feeds both the `{unsubscribe_url}` placeholder and the `List-Unsubscribe` MIME header. A silent break corrupts every campaign's unsubscribe flow and breaks RFC 8058 one-click compliance. Same fragility class as `billing_url`; same fix.

### D4. Extend `SystemSettings.clean()` to validate `email_footer_text` `href` schemes

`SystemSettings.clean()` already exists (`apps/mailing/models.py:120`) and validates that `email_sending_start_time != email_sending_end_time`. Extend the same method (called automatically by `ModelAdmin` and `full_clean()`) to scan `email_footer_text` for any `href="..."` or `href='...'` value. If the value doesn't start with `http://`, `https://`, or `mailto:`, raise `ValidationError` with the offending fragment and its line number. Allowlist-based, conservative: rejects javascript:, data:, relative URLs, and bare paths. Relative paths in particular were a problem — they only work in the HTML rendered on the same origin, not in an email client.

Trade-off: this only fires on admin save and on `full_clean()`. It does not protect against admin copy-pasting a broken absolute URL like `https://stripe.billing.nonexistent`. Acceptable — full URL liveness is outside scope, and the test harness catches missing routes anyway.

### D5. Test harness: per-template URL resolver assertion

Pattern, applied once per email template:

```python
# in test_all_emails_branded.py or a new test_email_links.py
def test_payment_receipt_billing_url_resolves(...):
    send_payment_receipt_email(...)
    html = mail.outbox[0].alternatives[0][0]
    expected = abs_url("billing_portal")  # or reverse(...)
    assert expected in html
```

A single new test module (`apps/mailing/tests/test_email_links.py`) walks every system email task, triggers it, and asserts each URL variable in the rendered body matches the corresponding `abs_url()` value. If a route is renamed without updating the task, the assertion fails.

### D6. Drop the dead `oauth_url` context variable

`apps/accounts/tasks.py:19,23` builds `oauth_url` and passes it to the welcome template, but `templates/email/welcome.html` and `welcome.txt` never reference it. Remove from the context dict. Remove the matching `oauth_url: "/"` line in `test_all_emails_branded.py:10`.

### D7. Add a clickable dashboard link to `campaign_paused_notification`

`templates/email/campaign_paused_notification.html` and `.txt` currently say "Por favor, revisa tu dashboard para más detalles." with no link. Add a `dashboard_url` (built via `abs_url("dashboard")`) to the `send_campaign_paused_notification` context and render it as a clickable link in the HTML and an inline URL in the plain-text twin. This is a missing-link fix, not a broken-link fix — the text already directs the user to the dashboard, but forces a manual copy-paste.

## Risks / Trade-offs

- **[R] `billing_portal` no longer `@require_POST` — could a malicious site force a user to trigger Stripe API calls?** → Mitigation: `@login_required` already gates access; CSRF is not needed for a GET that only reads and redirects. The Stripe call is read-only/idempotent (creates a portal session, no state mutation on the FastJob side). No protected resource is created or destroyed.
- **[R] `abs_url()` requires a registered view name at runtime** → Mitigation: `reverse()` raises `NoReverseMatch` immediately. Tests will catch any task that passes a typo. Acceptable — better than a silent 404.
- **[R] `SystemSettings.email_footer_text` validation is allowlist-based and may reject legitimate schemes (e.g., `tel:`, `sms:`)** → Mitigation: allowlist is `{http, https, mailto}` only. Phone/SMS links in the footer are not a current need; if they become one, the allowlist is one line to extend. Documented in `clean()` docstring.
- **[R] The new tests run the full email-render path, which depends on `SystemSettings.get()` and a seeded footer/logo** → Mitigation: tests use the existing `email_template` and other fixtures; the `cfg.email_footer_text` default is the shipped Spanish footer (line 62 model, line 35 of the seed migration). If the seed ever changes, the test will still pass as long as the admin form accepts it.
- **[R] `SITE_SCHEME` defaults to `https` in dev** → Mitigation: unchanged behavior; the `SITE_DOMAIN` placeholder check at `config/settings.py:368-383` already blocks production with a misconfig.
- **[R] Footer validation is admin-side only — existing rows with stale `href`s are not back-checked** → Mitigation: out of scope; admin will hit the error on next save. No data migration needed.

## Migration Plan

1. Land the code changes in one PR: helper, task migrations, view decorator, model `clean()`, tests, fixture cleanup.
2. No DB migration. No data backfill.
3. Rollback: revert the PR. The receipt email reverts to the broken link, which is the pre-change state — no worse than today.
4. Deployment: zero-downtime. New code is only exercised when an email is generated (i.e., on signup, purchase, OAuth link, low-credits threshold, account deletion) or when the admin opens the system-settings form.
5. Smoke test post-deploy: trigger each task in a Celery worker (or call the task `.apply()` in a shell) and confirm the rendered body contains the expected `abs_url()` value for the registered routes.

## Open Questions

- Should the billing-portal route slug also be renamed `portal` → `billing` for end-user-friendliness? Defer to a follow-up; not required to fix the bug and the new helper makes a rename low-cost later.
- Should the `email_footer_text` allowlist be configurable via settings (so new schemes can be enabled per environment)? Defer; YAGNI for now.
- Should the `abs_url()` helper be exposed in templates (e.g., as a `{% load %}` tag) for any future template-side use? Defer; current call sites are all Python.
