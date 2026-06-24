## ADDED Requirements

### Requirement: abs_url Is the Single Source of Truth for System URLs

`apps.core.urls.abs_url(viewname, *args, **kwargs)` MUST exist and be the only mechanism by which Python code (Celery tasks, views, management commands) constructs an absolute URL to a FastJob view. The helper MUST:
- Accept a Django URL view name plus any positional or keyword arguments needed to `reverse()` it.
- Use `django.urls.reverse()` to resolve the path component, so a non-existent view name raises `NoReverseMatch` immediately.
- Prefix the path with `f"{settings.SITE_SCHEME}://{settings.SITE_DOMAIN}"` to produce a fully qualified absolute URL.
- Be importable as `from apps.core.urls import abs_url`.

The Celery tasks that send system emails (`apps.accounts.tasks.send_welcome_email`, `apps.accounts.tasks.send_account_deleted_email`, `apps.accounts.tasks.send_oauth_link_email`, `apps.payments.tasks.send_payment_receipt_email`, `apps.mailing.tasks.send_low_credits_warning`, `apps.mailing.tasks.send_campaign_paused_notification`) MUST call `abs_url()` for every URL they embed in email context. The campaign engine (`apps.mailing.engine.send_cv_email`) MUST call `abs_url("unsubscribe", log.unsubscribe_token)` for the `unsubscribe_url` injected into the `{unsubscribe_url}` placeholder and the `List-Unsubscribe` MIME header. String concatenation with `settings.SITE_SCHEME` / `settings.SITE_DOMAIN` in those tasks and in `send_cv_email` MUST be removed.

#### Scenario: abs_url returns a fully qualified URL
- **GIVEN** `SITE_SCHEME = "https"` and `SITE_DOMAIN = "example.com"`
- **AND** the route `name="dashboard"` is registered at `/dashboard/`
- **WHEN** `abs_url("dashboard")` is called
- **THEN** it returns `"https://example.com/dashboard/"`.

#### Scenario: abs_url raises NoReverseMatch for unknown view
- **WHEN** `abs_url("does_not_exist")` is called
- **THEN** `django.urls.NoReverseMatch` is raised.

#### Scenario: A new system email task uses abs_url
- **WHEN** a new Celery task under `apps.accounts.tasks`, `apps.payments.tasks`, or `apps.mailing.tasks` needs to embed a URL in an email
- **THEN** the task MUST call `abs_url(viewname, ...)`.
- **AND** the code review checklist (or the new test harness) MUST fail if the task contains a literal `settings.SITE_DOMAIN` concatenation.

### Requirement: Test Harness Verifies System Email URL Resolution

A dedicated test module (proposed location: `apps/mailing/tests/test_email_links.py`) MUST walk every system email task, invoke it with appropriate fixtures, render the resulting email, and assert that each URL variable in the rendered body equals the value produced by `abs_url()` for the corresponding registered view name. The test module MUST cover at least:

| Email | URL variables to assert |
|---|---|
| `welcome` | `dashboard_url` |
| `payment_receipt` | `dashboard_url`, `billing_url` |
| `oauth_linked` | `dashboard_url` |
| `low_credits_warning` | `packages_url` |
| `account_deleted` | `home_url` |
| `campaign_paused_notification` | `dashboard_url` |
| campaign body (`send_cv_email`) | `unsubscribe_url` (in rendered body AND `List-Unsubscribe` header) |

If a new system email is added with URL variables, this test module MUST be extended in the same change. The test harness MAY also assert that the rendered body does not contain the literal substring `settings.SITE_DOMAIN` or raw `f"{settings.SITE_SCHEME}://"`, to detect any string-concatenation regression.

#### Scenario: Harness passes for current system emails
- **WHEN** `pytest apps/mailing/tests/test_email_links.py` is run on a clean checkout
- **THEN** all assertions pass.

#### Scenario: Harness catches a route rename
- **GIVEN** the `dashboard` route is renamed to `panel` in `apps.dashboard.urls`
- **AND** `apps.accounts.tasks.send_welcome_email` is updated to call `abs_url("panel")`
- **WHEN** the test harness runs
- **THEN** the welcome test passes (because `abs_url("panel")` is correct).
- **WHEN** a hypothetical other task still calls `abs_url("dashboard")`
- **THEN** that task's test fails with `NoReverseMatch`.

#### Scenario: Harness catches a missing URL variable in the template
- **GIVEN** a new email template introduces a `terms_url` variable
- **AND** the new task is wired up but the test module is not updated
- **WHEN** the test harness runs
- **THEN** the harness either fails (because the new variable is asserted to match `abs_url("terms")`) or, if the harness is non-exhaustive, the code review process MUST flag the omission.
