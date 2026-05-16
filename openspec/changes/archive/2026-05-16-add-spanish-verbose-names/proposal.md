# Change: Add Spanish verbose names to all admin-facing model fields

## Why
Every Django model field without an explicit `verbose_name` renders its
Python identifier in title-case English in the admin (e.g.
`global_send_interval_minutes` → "Global send interval minutes"). With
`LANGUAGE_CODE = "es"` and a Spanish-speaking team, these English labels
are incorrect and confusing. A handful of admin customisations
(`short_description`, fieldset headers, fieldset descriptions) also still
carry English text or expose raw Python key names. This change replaces
every English-facing admin label with a correct Spanish string, hardcoded
directly in the source — no `.po` file or i18n framework is required.

## What Changes

### `apps/mailing/models.py`
- `SystemSettings`: add `verbose_name` to all 5 fields
  (`global_send_interval_minutes`, `company_cooldown_hours`,
  `max_emails_per_day_per_user`, `initial_free_credits`,
  `hidden_credit_multiplier`)
- `EmailTemplate`: add `verbose_name` to all 5 fields
  (`name`, `subject`, `body_html`, `is_active`, `created_at`)
- `MailingLog`: add `verbose_name` to all 11 fields
  (`user`, `company`, `email_template`, `cv`, `cv_download_token`,
  `unsubscribe_token`, `sent_at`, `status`, `error_message`,
  `company_email_snapshot`, `unsubscribed_at`)

### `apps/mailing/admin.py`
- `SystemSettingsAdmin` fieldset descriptions: replace raw Python key
  names with fully Spanish prose (no identifier leakage)
- `preview_link.short_description`: `"Preview"` → `"Vista previa"`

### `apps/accounts/models.py`
- `User`: add `verbose_name` to 5 fields without one
  (`is_campaign_active`, `active_cv`, `area_filters`, `location_filters`,
  `stripe_customer_id`)
- `CV`: add `verbose_name` to all 4 fields
  (`user`, `file`, `name`, `created_at`)

### `apps/accounts/admin.py`
- `UserAdmin` fieldset header: `"FastJob"` → `"Datos FastJob"`

### `apps/companies/models.py`
- `Area`: add `verbose_name` to `name`
- `Location`: add `verbose_name` to `name`
- `Company`: add `verbose_name` to all 13 fields
  (`email`, `name`, `area`, `location`, `address`, `zip_code`,
  `province`, `community`, `phone`, `fax`, `website`,
  `last_received_at`, `created_at`)
- `Blacklist`: add `verbose_name` to all 3 fields
  (`email`, `added_at`, `reason`)
- `CompanyImportBatch`: add `verbose_name` to all 12 fields
  (`file`, `status`, `upload_uuid`, `original_filename`, `total_rows`,
  `processed_rows`, `created_count`, `updated_count`,
  `blacklisted_skipped`, `error_log`, `created_at`, `updated_at`)

### `apps/payments/models.py`
- `StripePayment`: add `verbose_name` to all 9 fields
  (`user`, `package`, `stripe_session_id`, `stripe_payment_intent`,
  `amount_eur`, `credits_granted`, `status`, `created_at`,
  `completed_at`)

### `apps/core/models.py`
- `SystemConfig.save_emails_to_sent_folder`: add `verbose_name`
  (`"Guardar en carpeta Enviados"`) and remove the trailing English
  word from the `help_text` (`(Sent)` → dropped)

## Impact
- Affected specs: `accounts`, `mailing`, `companies`, `pricing`
- Affected code:
  - `apps/accounts/models.py`, `apps/accounts/admin.py`
  - `apps/mailing/models.py`, `apps/mailing/admin.py`
  - `apps/companies/models.py`
  - `apps/payments/models.py`
  - `apps/core/models.py`
- No database migrations required (verbose_name is metadata only)
- No template changes required
- No test changes required (no test covers admin label text)
