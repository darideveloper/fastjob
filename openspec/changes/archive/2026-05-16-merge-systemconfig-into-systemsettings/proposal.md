# Change: Merge SystemConfig into SystemSettings

## Why
`SystemConfig` in `apps/core` holds a single field (`save_emails_to_sent_folder`) that
is functionally a mailing engine setting. Having it in a separate Django app means admins
must navigate to two different admin sections (`/admin/core/systemconfig/` and
`/admin/mailing/systemsettings/`) to manage all system-level toggles. Consolidating into
`SystemSettings` gives a single authoritative settings page at
`/admin/mailing/systemsettings/1/change/` and removes an orphaned dependency between
`apps.mailing.engine` and `apps.core`.

## What Changes
- `save_emails_to_sent_folder` is added as a new `BooleanField` on `SystemSettings`
  (`apps/mailing/models.py`) with the same default (`False`) and Spanish help-text.
- A data migration in `apps/mailing` copies the existing value from
  `core_systemconfig` (pk=1) to `mailing_systemsettings` (pk=1) before the source
  table is dropped, preserving any live configuration.
- A follow-up migration in `apps/core` removes `SystemConfig` and its table.
- `apps/mailing/engine.py` imports `SystemSettings` instead of `SystemConfig` for the
  `save_emails_to_sent_folder` check (two call sites: lines ~291 and ~328).
- `apps/core/models.py` and `apps/core/admin.py` are stripped of `SystemConfig` /
  `SystemConfigAdmin`. The `core` app itself is kept (it owns `storage_utils.py` and
  the `clear_company_data` management command).
- Tests in `apps/mailing/tests/test_engine.py` are updated to seed `SystemSettings`
  instead of `SystemConfig` (seven call sites).
- Tests in `apps/core/tests/test_models.py` that cover `SystemConfig` are removed.

## Impact
- **Affected specs**: `mailing`
- **Affected code**:
  - `apps/mailing/models.py` — add field to `SystemSettings`
  - `apps/mailing/migrations/` — field migration + data migration (one file)
  - `apps/core/migrations/` — model removal migration
  - `apps/mailing/engine.py` — swap import and two `SystemConfig.get()` calls
  - `apps/mailing/admin.py` — add `save_emails_to_sent_folder` to `SystemSettingsAdmin`
    field list
  - `apps/mailing/tests/test_engine.py` — update seven `SystemConfig` seed lines
  - `apps/core/models.py` — delete `SystemConfig` class
  - `apps/core/admin.py` — delete `SystemConfigAdmin` registration
  - `apps/core/tests/test_models.py` — delete `test_system_config_singleton`
- **No breaking changes**: the DB value is copied by the data migration; the admin URL
  changes from `/admin/core/systemconfig/1/change/` to
  `/admin/mailing/systemsettings/1/change/` (no external system depends on the old URL).
- **No template, API, or frontend changes** required.
