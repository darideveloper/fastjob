## ADDED Requirements

### Requirement: Spanish verbose names on User fields
The `User` model (`apps/accounts/models.py`) SHALL have explicit Spanish `verbose_name` on every field that previously lacked one.

| Field | verbose_name |
|---|---|
| `is_campaign_active` | `"Campaña activa"` |
| `active_cv` | `"CV activo"` |
| `area_filters` | `"Filtros de sector"` |
| `location_filters` | `"Filtros de localidad"` |
| `stripe_customer_id` | `"ID de cliente Stripe"` |

Fields that already carry a Spanish `verbose_name`
(`credits_remaining`, `total_purchased_credits`, `campaign_pause_reason`)
are unaffected.

#### Scenario: User change form shows Spanish labels for FastJob fields
- **WHEN** a staff user opens `/admin/accounts/user/<id>/change/`
- **THEN** the FastJob fieldset labels for the five fields above match
  their Spanish verbose names
- **AND** no English auto-generated label is visible

### Requirement: Spanish verbose names on CV fields
All fields of `CV` (`apps/accounts/models.py`) SHALL declare an explicit
`verbose_name` in Spanish.

| Field | verbose_name |
|---|---|
| `user` | `"Usuario"` |
| `file` | `"Archivo"` |
| `name` | `"Nombre"` |
| `created_at` | `"Creado el"` |

#### Scenario: CV change form shows Spanish labels
- **WHEN** a staff user opens `/admin/accounts/cv/<id>/change/`
- **THEN** each field label matches the Spanish string from the table above

### Requirement: UserAdmin FastJob fieldset header is Spanish
`UserAdmin` (`apps/accounts/admin.py`) SHALL use `"Datos FastJob"` as the fieldset header instead of the English string `"FastJob"`.

#### Scenario: User change form shows "Datos FastJob" section header
- **WHEN** a staff user opens `/admin/accounts/user/<id>/change/`
- **THEN** the custom fieldset header reads `"Datos FastJob"`
- **AND** the previous English-only header `"FastJob"` is not rendered
