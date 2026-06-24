## 1. Add abs_url helper

- [x] 1.1 Create `apps/core/urls.py` (new module) with `abs_url(viewname, *args, **kwargs)` that wraps `django.urls.reverse()` and prefixes with `f"{settings.SITE_SCHEME}://{settings.SITE_DOMAIN}"`.
- [x] 1.2 Add a unit test in `apps/core/tests/test_abs_url.py` (new) covering: (a) basic round-trip, (b) `NoReverseMatch` on unknown name, (c) respects `SITE_SCHEME`/`SITE_DOMAIN` overrides via `override_settings`, (d) positional args pass-through for UUID-token routes.

## 2. Fix billing URL + GET-accessible billing portal

- [x] 2.1 In `apps/payments/tasks.py:22`, replace the literal `/payments/billing/` with the path returned by `reverse("billing_portal")`, built via `abs_url("billing_portal")`.
- [x] 2.2 In `apps/payments/views.py`, drop the `@require_POST` decorator on `billing_portal` (keep `@login_required`). Confirm no existing caller depends on POST semantics.
- [x] 2.3 In `apps/payments/tests/test_billing_portal.py`, add a test that issues GET to the URL via `client.get(reverse("billing_portal"))` and asserts a 302 redirect (to Stripe), NOT a 405. (`test_billing_portal_accepts_get_from_email_click`)

## 3. Migrate system email URL construction to abs_url

- [x] 3.1 In `apps/accounts/tasks.py:send_welcome_email`, replace `dashboard_url` and `oauth_url` literal f-strings with `abs_url("dashboard")`. Then drop the unused `oauth_url` from the context dict entirely.
- [x] 3.2 In `apps/accounts/tasks.py:send_account_deleted_email`, replace `home_url` literal with `abs_url("home")`.
- [x] 3.3 In `apps/accounts/tasks.py:send_oauth_link_email`, replace `dashboard_url` literal with `abs_url("dashboard")`.
- [x] 3.4 In `apps/payments/tasks.py:send_payment_receipt_email`, replace both `dashboard_url` and `billing_url` with `abs_url(...)` calls (billing uses `abs_url("billing_portal")`).
- [x] 3.5 In `apps/mailing/tasks.py:send_low_credits_warning`, replace `packages_url` literal with `abs_url("payment_packages")`.
- [x] 3.6 In `apps/mailing/engine.py:send_cv_email`, replace the `base_url` + `unsubscribe_url` string-concat (lines 374-375) with `abs_url("unsubscribe", log.unsubscribe_token)`. This URL feeds both the `{unsubscribe_url}` body placeholder and the `List-Unsubscribe` MIME header. Removed the now-dead `base_url` local.
- [x] 3.7 In `apps/mailing/tasks.py:send_campaign_paused_notification`, add `dashboard_url = abs_url("dashboard")` to the context so the paused-notification email can link to the dashboard (see task 6.4).

## 4. Extend SystemSettings.clean() with footer href validation

- [x] 4.1 In `apps/mailing/models.py`, EXTEND the existing `SystemSettings.clean()` method (already at line 120, currently validates send-times) to also scan `email_footer_text` for `href="…"` / `href='…'` and raise `ValidationError` if the value does not start with `http://`, `https://`, or `mailto:`. The error message must include the offending line and scheme. Implemented as a private helper `_validate_footer_href_schemes()` called from `clean()`.
- [x] 4.2 In `apps/mailing/tests/test_models.py`, add tests asserting: (a) an https link passes, (b) a `mailto:` link passes, (c) a `javascript:` link fails, (d) a relative `/path` fails, (e) the error message includes the line number, (f) the existing send-time equality validation still works (no regression). (6 new tests + 3 existing = 9 total.)

## 5. Add the email-link regression test harness

- [x] 5.1 Create `apps/mailing/tests/test_email_links.py` with one test per system email that:
  - Calls the relevant task (e.g., `send_welcome_email`).
  - Pulls the rendered HTML from `mail.outbox[0].alternatives`.
  - Asserts each URL variable in the template body matches `abs_url("<viewname>")`.
  - Covers: `welcome` (dashboard_url), `payment_receipt` (dashboard_url, billing_url), `oauth_linked` (dashboard_url), `low_credits_warning` (packages_url), `account_deleted` (home_url), `campaign_paused_notification` (dashboard_url). (7 tests total.)
- [x] 5.2 Add a sanity assertion (`_assert_no_string_concat`) to each test that the rendered body does NOT contain the substring `settings.SITE_DOMAIN` or the literal `f"{settings.SITE_SCHEME}://"` (catches string-concatenation regression).
- [x] 5.3 Add a test for the campaign engine's `unsubscribe_url`: call `send_cv_email` with mocked HTTP, decode the MIME body (or read the `List-Unsubscribe` header as `test_engine.py:806` already does), and assert the URL equals `abs_url("unsubscribe", log.unsubscribe_token)`. (`test_campaign_engine_unsubscribe_url_resolves`)

## 6. Clean up dead references, stale fixtures, and add missing links

- [x] 6.1 In `apps/mailing/tests/test_all_emails_branded.py:10`, remove the `"oauth_url": "/"` line from the welcome test fixture. Also add `"dashboard_url": "/"` to the `campaign_paused_notification` fixture (required because the template now references `{{ dashboard_url }}`).
- [x] 6.2 In `apps/payments/tests/test_payment_email.py`, add a test (`test_receipt_email_billing_url_resolves_to_registered_route`) that asserts the rendered HTML and plain-text body contain the value of `abs_url("billing_portal")` (regression guard for the actual bug being fixed). Also asserts the old broken `/payments/billing/` path does NOT appear.
- [x] 6.3 In `apps/mailing/tests/test_engine.py:806,830`, update the `expected_url` assertions to use `abs_url("unsubscribe", log.unsubscribe_token)` instead of the inline f-string, so the test harness catches drift on the unsubscribe route too. Removed the now-dead local `from django.conf import settings` imports.
- [x] 6.4 In `templates/email/campaign_paused_notification.html`, add `<p><a href="{{ dashboard_url }}">Ir a tu dashboard</a></p>` after the "revisa tu dashboard" line. In `templates/email/campaign_paused_notification.txt`, add `Dashboard: {{ dashboard_url }}` at the end.
- [x] 6.5 In `apps/mailing/tests/test_cv_email_branded.py`, replace `MagicMock()` log argument with a real `MailingLog.objects.create(...)` row. Required because `abs_url("unsubscribe", log.unsubscribe_token)` now validates the UUID format via `reverse()`, and a `MagicMock` is not a valid UUID.
- [x] 6.6 Run `pytest` and confirm the full suite passes (434 passed). `manage.py check` reports no issues.

## 7. Documentation and verification

- [x] 7.1 Update `openspec/specs/payments/spec.md` — handled by this change's delta spec at archive time (no extra doc work required now).
- [x] 7.2 Run `python manage.py check` and confirm no system check errors (0 issues).
- [ ] 7.3 Manually trigger one of each email task in a Celery worker (or via `task.apply()`) and inspect the rendered body to confirm the URLs are correct and clickable. Smoke test: log into the admin, set `email_footer_text` to `<a href="https://example.com">x</a>` (saves), then to `<a href="javascript:alert(1)">x</a>` (must fail). **Status: not yet performed — requires a running dev server and manual admin interaction. Automated coverage is provided by T5 (test_email_links.py) and T4.2 (footer validation tests).**
