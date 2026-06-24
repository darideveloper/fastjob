## Why

The payment receipt email sent to every paying user contains a "Manage billing in Stripe" link that points to `/payments/billing/`, but the actual route is mounted at `/payments/portal/`. Clicking the link returns a 404, breaking a critical post-purchase user journey. A broader audit of system emails also surfaced related issues: hardcoded URL paths across seven email-URL call sites (six task sites plus the campaign engine's `unsubscribe_url` — all fragile to future route renames), a POST-only billing portal view that can't be reached from an email click, an unused `oauth_url` context variable, and no automated test asserting that the URLs embedded in system emails actually resolve. The receipt link bug is the only one that produces a user-visible 404 today; the rest are latent risks that should be fixed in the same change to prevent the next instance of the same class of bug.

## What Changes

- Fix the broken `billing_url` in `apps/payments/tasks.py:22` so the payment receipt email points to the real billing portal route.
- Drop `@require_POST` from `apps/payments/views.py:billing_portal` (or change the email link to a GET-friendly landing page) so a direct email click can reach the Stripe billing portal.
- Introduce a single `abs_url(name, *args)` helper under `apps/core/` and replace the seven `f"{settings.SITE_SCHEME}://{settings.SITE_DOMAIN}/…"` email-URL call sites with it, so URL renames cannot silently break emails. The seven sites: `apps/accounts/tasks.py` (×3: welcome `dashboard_url`, account_deleted `home_url`, oauth_linked `dashboard_url`), `apps/payments/tasks.py` (×2: `dashboard_url`, `billing_url`), `apps/mailing/tasks.py` (×1: low_credits `packages_url`), and `apps/mailing/engine.py:374-375` (the `unsubscribe_url` injected into campaign bodies and the `List-Unsubscribe` header). The dead `oauth_url` in the welcome context is removed rather than migrated.
- Remove the dead `oauth_url` context variable from `apps/accounts/tasks.py:send_welcome_email` and from the test fixture in `apps/mailing/tests/test_all_emails_branded.py:10`.
- Add regression tests asserting that every URL embedded in a system email (`welcome`, `payment_receipt`, `oauth_linked`, `low_credits_warning`, `account_deleted`, `campaign_paused_notification`) and the campaign engine's `unsubscribe_url` resolves via `reverse()` to a registered route.
- Extend the existing `SystemSettings.clean()` method (`apps/mailing/models.py:120`) with validation of `email_footer_text` that rejects values containing an `href=` whose target does not start with `http://`, `https://`, or `mailto:`.
- Add a clickable `dashboard_url` link to `campaign_paused_notification.html` / `.txt` (currently the text says "revisa tu dashboard" with no link — a missing link, not a broken one).

## Capabilities

### New Capabilities
- `email-link-resilience`: Cross-cutting capability covering the helper, the test harness, and the footer-text validation that ensure URLs embedded in system emails always resolve to real routes.

### Modified Capabilities
- `mailing`: REQUIREMENTS change — system email templates (`welcome`, `payment_receipt`, `oauth_linked`, `low_credits_warning`, `account_deleted`, `campaign_paused_notification`) MUST emit URLs that resolve to registered routes; the campaign engine's `unsubscribe_url` MUST resolve; the branded layout's `footer_text` MUST be validated for safe `href` schemes; the welcome context MUST NOT carry dead variables.
- `payments`: REQUIREMENTS change — the `billing_portal` view MUST be reachable by GET (email-click safe) and the `send_payment_receipt_email` task MUST emit a working `billing_url`.

## Impact

- **Code**:
  - `apps/payments/tasks.py` — `billing_url` string fix.
  - `apps/payments/views.py` — drop `@require_POST` on `billing_portal` (and ensure the view does its own idempotent work or remains a no-op on GET before redirecting to Stripe).
  - `apps/payments/urls.py` — possibly rename route slug for consistency (deferred decision; see design).
  - `apps/accounts/tasks.py` — drop `oauth_url` from welcome context.
  - `apps/accounts/tasks.py`, `apps/payments/tasks.py`, `apps/mailing/tasks.py`, `apps/mailing/engine.py` — replace literal URL construction with helper (seven call sites total, including the `unsubscribe_url` in the campaign engine).
  - `apps/core/urls.py` (new) — `abs_url()` helper.
  - `apps/mailing/models.py` — extend existing `SystemSettings.clean()` (already validates send-times) with `email_footer_text` `href` scheme validation.
  - `apps/mailing/tasks.py` — add `dashboard_url` to `send_campaign_paused_notification` context.
  - `templates/email/campaign_paused_notification.html` / `.txt` — add clickable dashboard link.
  - `apps/payments/tests/test_payment_email.py` — assert `billing_url` resolves to `reverse("billing_portal")`.
  - `apps/mailing/tests/test_all_emails_branded.py` — drop `oauth_url`, add `dashboard_url` to the paused-notification fixture.
  - `apps/mailing/tests/test_engine.py:806,830` — update expected `unsubscribe_url` assertions to use `abs_url()`.
  - `apps/mailing/tests/test_cv_email_branded.py` — replace `MagicMock()` log with a real `MailingLog` row (required because `abs_url()` validates the UUID format via `reverse()`).
  - `apps/mailing/tests/test_email_links.py` (new) — regression harness covering welcome, oauth_linked, low_credits_warning, account_deleted, campaign_paused_notification, and campaign-engine `unsubscribe_url` URL resolution.
  - `apps/accounts/tests/` — no new file; welcome/oauth-linked `dashboard_url` resolution is covered by `test_email_links.py` (the proposal's "new or existing" option).
- **APIs / behavior**:
  - `billing_portal` view no longer requires POST. Current POST callers (if any) still work.
  - `SystemSettings.email_footer_text` admin save MAY fail validation on unsafe `href` schemes (admin UX change; messages surface the offending line).
- **Dependencies**: none. No new packages.
- **Data / migrations**: none. `email_footer_text` validation runs on `full_clean()` only; no schema change.
- **Out of scope**: the user-authored template BODY content (the HTML a staff user types into `EmailTemplate.body_html`) — that is free-form content, not a system-built URL. The system-built `unsubscribe_url` VALUE injected into the `{unsubscribe_url}` placeholder IS in scope (it is built by `apps/mailing/engine.py`, not authored by the user). Stripe success/cancel/return URLs in `apps/payments/views.py:35,107` are out of scope (not email links) but are a follow-up candidate for the same `abs_url()` helper.
