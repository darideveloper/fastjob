# Proposal: Update Company Logo URL

Update the company logo URL across the codebase, database settings, and automated tests to ensure consistent branding using the new asset location.

## Why
The current logo URL (`https://raw.githubusercontent.com/daridev/fastjob/main/static/images/fastjob-logo.png`) points to a legacy repository/branch. Stakeholders have moved the official assets to a new location. We need to transition all references to: `https://raw.githubusercontent.com/darideveloper/fastjob/refs/heads/main/static/images/fastjob-logo.png`.

## What Changes
- **Models**: Update the `default` value for `SystemSettings.email_logo_url` in `apps/mailing/models.py` and align its `verbose_name` to `"URL del logo en emails"` to match the specification.
- **Migrations**: Create a new data migration to update the default value in the database schema, update the verbose name, and update the existing singleton record in the `mailing_systemsettings` table.
- **Tests**: Update hardcoded URL references in the following test files:
  - `apps/payments/tests/test_payment_email.py`
  - `apps/mailing/tests/test_paused_notification_branded.py`
  - `apps/mailing/tests/test_email_branding.py`
  - `apps/mailing/tests/test_cv_email_branded.py`
  - `apps/dashboard/tests/test_deletion_email.py`
  - `apps/accounts/tests/test_oauth_email.py`
- **Validation**: Run all affected tests to ensure they pass with the new URL.

## Technical Details
The change is straightforward but requires a data migration because the `email_logo_url` is stored in a database singleton. Simply changing the model default won't update the existing record created by previous migrations.
