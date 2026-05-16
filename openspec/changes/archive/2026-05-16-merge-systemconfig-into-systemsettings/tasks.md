## 1. Model

- [x] 1.1 In `apps/mailing/models.py`, add `save_emails_to_sent_folder = models.BooleanField(
       default=False, verbose_name="Guardar en carpeta Enviados", help_text="…")` to
       `SystemSettings`, after the existing `hidden_credit_multiplier` field.

## 2. Migrations

- [x] 2.1 Create `apps/mailing/migrations/0011_systemsettings_save_emails_to_sent_folder.py`
       that adds the field AND includes a `RunPython` data step: if `core_systemconfig`
       pk=1 exists, copy its `save_emails_to_sent_folder` value into
       `mailing_systemsettings` pk=1 (creating it if absent).
- [x] 2.2 Create `apps/core/migrations/0002_delete_systemconfig.py` that removes the
       `SystemConfig` model (drops the `core_systemconfig` table). This migration MUST
       declare a dependency on `mailing 0011` so the data is always migrated before the
       source table is dropped.

## 3. Engine

- [x] 3.1 In `apps/mailing/engine.py`, remove the line `from apps.core.models import
       SystemConfig` (line 30) and add a new import line `from apps.mailing.models import
       SystemSettings` (note: `SystemSettings` is NOT currently imported in engine.py —
       it must be added explicitly). Then replace the two
       `SystemConfig.get().save_emails_to_sent_folder` reads (lines ~291 and ~328) with
       `SystemSettings.get().save_emails_to_sent_folder`.

## 4. Admin

- [x] 4.1 In `apps/mailing/admin.py`, add `save_emails_to_sent_folder` to
       `SystemSettingsAdmin` so the field is visible and editable at
       `/admin/mailing/systemsettings/1/change/`.
- [x] 4.2 In `apps/core/admin.py`, remove the `SystemConfigAdmin` class and its
       `@admin.register(SystemConfig)` decorator (and the `from .models import
       SystemConfig` import).

## 5. Core model cleanup

- [x] 5.1 In `apps/core/models.py`, delete the entire `SystemConfig` class. If the file
       is now empty of user-defined code (only the `from django.db import models` import
       remains), remove that import too.

## 6. Tests

- [x] 6.1 In `apps/mailing/tests/test_engine.py`:
       a. Delete line 16 (`from apps.core.models import SystemConfig`) entirely.
       b. Add `SystemSettings` to the existing line 26 so it reads
          `from apps.mailing.models import MailingLog, SystemSettings` — do NOT add a
          separate `apps.mailing.models` import line as that would be a duplicate.
       c. Replace all seven `SystemConfig.objects.update_or_create(pk=1, defaults={...})`
          calls with `SystemSettings.objects.update_or_create(pk=1, defaults={...})`.
       d. Update the section comment at line 925 from
          `# Global Email Visibility Toggle (SystemConfig)` to
          `# Global Email Visibility Toggle (SystemSettings)`.
- [x] 6.2 In `apps/core/tests/test_models.py`, delete `test_system_config_singleton`
       (the `SystemConfig` model no longer exists). Keep the file if other tests remain;
       delete it entirely if it becomes empty.

## 7. Validation

- [x] 7.1 Run `python manage.py migrate --run-syncdb` (or `migrate`) — zero errors.
- [x] 7.2 Run `pytest apps/mailing/tests/test_engine.py -v` — all tests pass.
- [x] 7.3 Run `pytest apps/core/tests/ -v` — all remaining tests pass.
- [x] 7.4 Run `openspec validate merge-systemconfig-into-systemsettings --strict` — zero
       issues.
