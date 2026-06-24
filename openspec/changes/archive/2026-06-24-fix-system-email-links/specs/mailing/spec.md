## ADDED Requirements

### Requirement: System Email URLs Must Resolve to Registered Routes

Every URL embedded in a system email template rendered by `apps.mailing.email.render_branded_email` (and any direct sibling tasks under `apps.accounts.tasks` and `apps.payments.tasks`) MUST resolve to a registered Django route. The system MUST provide a regression test that, for each of the `welcome`, `payment_receipt`, `oauth_linked`, `low_credits_warning`, and `account_deleted` email templates, renders the email by calling its task and asserts that every URL variable in the rendered body matches the URL produced by `apps.core.urls.abs_url()` for the corresponding view name.

The regression test MUST fail if:
- A task builds a URL by string concatenation rather than calling `abs_url()`, OR
- `abs_url()` is called with a view name that is not registered, OR
- The template is updated to embed a new URL variable that the test harness does not cover.

#### Scenario: All system email URLs resolve after route rename
- **GIVEN** a system email task builds its `dashboard_url` via `abs_url("dashboard")`
- **WHEN** the `dashboard` view is renamed in `apps.dashboard.urls` (e.g., to `panel`) and the task is updated to call `abs_url("panel")` accordingly
- **THEN** the rendered email body still contains the correct absolute URL.
- **AND** the test harness passes.

#### Scenario: A typo in a view name fails the test harness
- **GIVEN** a task calls `abs_url("dhasboard")` (typo)
- **WHEN** the test harness runs
- **THEN** the harness fails with `django.urls.NoReverseMatch`, surfacing the typo before the email is ever sent.

#### Scenario: A string-concatenated URL is detected by the harness
- **GIVEN** a task regresses to `f"{SITE_SCHEME}://{SITE_DOMAIN}/dashboard/"` instead of `abs_url("dashboard")`
- **WHEN** the test harness runs and compares the email body to the expected value
- **THEN** the harness fails (the literal string does not match `abs_url()`'s output for the `dashboard` route).

### Requirement: Branded Email Footer Hrefs Use Safe Schemes

`SystemSettings.email_footer_text` is rendered into the branded email layout with the `|safe` filter and can therefore contain raw HTML, including `<a href="…">`. The model's `clean()` method MUST scan the stored text for any `href="…"` or `href='…'` value. If the value does not start with one of the allowed URL schemes — `http://`, `https://`, or `mailto:` — the `clean()` method MUST raise a `django.core.exceptions.ValidationError` naming the offending line and the disallowed scheme.

Allowed schemes: `http://`, `https://`, `mailto:`. All other schemes (including `javascript:`, `data:`, `tel:`, `sms:`, relative URLs, and bare paths) MUST be rejected.

#### Scenario: Admin saves footer with an http link
- **GIVEN** an admin opens `/admin/mailing/systemsettings/` and enters `<a href="https://example.com/terms">Terms</a>` in `email_footer_text`
- **WHEN** the form is submitted
- **THEN** the save succeeds and the footer renders unchanged in subsequent emails.

#### Scenario: Admin saves footer with a javascript: link
- **GIVEN** an admin enters `<a href="javascript:alert(1)">Click</a>` in `email_footer_text`
- **WHEN** the form is submitted
- **THEN** `clean()` raises `ValidationError`.
- **AND** the row is not saved.

#### Scenario: Admin saves footer with a relative href
- **GIVEN** an admin enters `<a href="/terms">Terms</a>` in `email_footer_text`
- **WHEN** the form is submitted
- **THEN** `clean()` raises `ValidationError` (relative URLs are not safe in emails, where the recipient's client resolves them against its own origin).
- **AND** the row is not saved.

#### Scenario: Admin saves footer with a mailto: link
- **GIVEN** an admin enters `<a href="mailto:support@example.com">Contact</a>` in `email_footer_text`
- **WHEN** the form is submitted
- **THEN** the save succeeds.

### Requirement: Welcome Email Context Has No Dead Variables

`send_welcome_email` in `apps.accounts.tasks` MUST NOT pass an `oauth_url` context variable (or any other variable that is not referenced by the `email/welcome.html` or `email/welcome.txt` templates). The context dict MUST contain exactly the variables the templates use.

#### Scenario: send_welcome_email context is template-minimal
- **WHEN** `send_welcome_email` is called and the rendered templates are inspected
- **THEN** every key in the context dict MUST appear at least once in `welcome.html` or `welcome.txt`.
- **AND** no template-only key is missing from the context.

#### Scenario: oauth_url is removed
- **GIVEN** the `oauth_url` was previously in the welcome context but unused by the templates
- **WHEN** the change is applied
- **THEN** `apps.accounts.tasks.send_welcome_email` no longer references or passes `oauth_url`.
- **AND** the test fixture in `apps.mailing.tests.test_all_emails_branded` no longer supplies `oauth_url`.

### Requirement: Campaign Paused Notification Has a Clickable Dashboard Link

`send_campaign_paused_notification` in `apps.mailing.tasks` MUST include a `dashboard_url` in its email context, built via `abs_url("dashboard")`. The `email/campaign_paused_notification.html` template MUST render this URL as a clickable `<a href="{{ dashboard_url }}">` link alongside the existing "revisa tu dashboard" text. The `email/campaign_paused_notification.txt` template MUST include the URL as inline text.

#### Scenario: Paused notification email contains a working dashboard link
- **GIVEN** a user's campaign is paused for any reason
- **WHEN** `send_campaign_paused_notification.delay(user.pk, reason)` runs
- **THEN** the rendered HTML body contains `<a href="{{ dashboard_url }}">` whose value equals `abs_url("dashboard")`.
- **AND** the rendered plain-text body contains the same URL as inline text.

#### Scenario: Dashboard link in paused notification resolves
- **WHEN** the recipient clicks the dashboard link in the paused-notification email
- **THEN** the URL resolves to the registered `dashboard` route (or the login redirect if unauthenticated).
