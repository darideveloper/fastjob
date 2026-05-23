## ADDED Requirements

### Requirement: SystemSettings exposes a configurable displayed-sends floor
`SystemSettings` (`apps/mailing/models.py`) SHALL expose an integer field
`displayed_sends_floor` (default `0`, minimum `0`) that allows administrators
to set a minimum value for the sends count shown publicly on the pricing page.

The field MUST be:
- Registered and editable in the Django admin at `/admin/mailing/systemsettings/`
- `verbose_name` = `"Mínimo de envíos mostrados"` in Spanish
- `help_text` = `"Si el número real de envíos exitosos es menor que este valor, se mostrará este valor en la página de paquetes. Usar 0 para mostrar siempre el valor real."`
- Non-negative (value ≥ 0)
- A Django migration MUST be created to add the column with the default.

The `packages` view in `apps/payments/views.py` MUST read this value via
`SystemSettings.get().displayed_sends_floor` and use it to compute
the final `successful_sends_count` context variable as
`max(real_count, displayed_sends_floor)`.

#### Scenario: Admin can set the floor value
- **GIVEN** a Django staff user with permission to change `SystemSettings`
- **WHEN** they open `/admin/mailing/systemsettings/` and set
  `Mínimo de envíos mostrados` to `500` and save
- **THEN** `SystemSettings.get().displayed_sends_floor` returns `500`
- **AND** the next request to `GET /payments/paquetes/` reflects this value

#### Scenario: Default floor is zero (no artificial inflation)
- **GIVEN** a freshly seeded database with no manual admin configuration
- **WHEN** `SystemSettings.get().displayed_sends_floor` is read
- **THEN** the returned value is `0`
- **AND** the pricing page trust signal is hidden when real sent count is also `0`

#### Scenario: Migration adds column without data loss
- **WHEN** the migration is applied on an existing database
- **THEN** all existing `SystemSettings` rows gain `displayed_sends_floor = 0`
- **AND** no existing field values are altered
