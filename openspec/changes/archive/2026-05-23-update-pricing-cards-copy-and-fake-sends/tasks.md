## 1. Model & Migration

- [x] 1.1 Add `displayed_sends_floor = models.IntegerField(default=0, ...)` to `SystemSettings` in `apps/mailing/models.py`
- [x] 1.2 Run `python manage.py makemigrations mailing` to generate the migration
- [x] 1.3 Verify the migration contains only `AddField` for `displayed_sends_floor` with `default=0`

## 2. View Logic

- [x] 2.1 Update `packages()` in `apps/payments/views.py` to import `SystemSettings` and compute `successful_sends_count = max(real_count, SystemSettings.get().displayed_sends_floor)`

## 3. Admin

- [x] 3.1 Add a "Página de Paquetes" fieldset to `SystemSettingsAdmin` in `apps/mailing/admin.py` exposing `displayed_sends_floor`

## 4. Template

- [x] 4.1 In `templates/payments/packages.html`, change `CVs enviados` to `CVs enviados exitosamente` in the feature list `<li>`
- [x] 4.2 Remove the per-card trust signal badge (`✓ +N envíos exitosos en la plataforma`) from inside each card's price block; keep only the footer trust bar

## 5. Validation

- [x] 5.1 Run `python manage.py migrate` and confirm no errors
- [x] 5.2 Set `displayed_sends_floor = 500` via `/admin/mailing/systemsettings/` and verify the pricing page shows `500` when real count < 500
- [x] 5.3 Set `displayed_sends_floor = 0` and verify trust signal is hidden when real count is also 0
- [x] 5.4 Run the test suite: `pytest apps/payments/ apps/mailing/ -x` and confirm all tests pass
