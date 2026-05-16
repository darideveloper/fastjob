## ADDED Requirements

### Requirement: Spanish verbose names on SystemSettings fields
All fields of `SystemSettings` (`apps/mailing/models.py`) SHALL declare an
explicit `verbose_name` in Spanish so Django admin displays readable Spanish
labels instead of auto-generated English title-case identifiers.

| Field | verbose_name |
|---|---|
| `global_send_interval_minutes` | `"Intervalo de envío (minutos)"` |
| `company_cooldown_hours` | `"Enfriamiento por empresa (horas)"` |
| `max_emails_per_day_per_user` | `"Máximo de envíos por usuario al día"` |
| `initial_free_credits` | `"Envíos gratuitos iniciales"` |
| `hidden_credit_multiplier` | `"Multiplicador oculto de envíos"` |

#### Scenario: SystemSettings change form shows Spanish labels
- **WHEN** a staff user opens `/admin/mailing/systemsettings/1/change/`
- **THEN** each field label is the Spanish string from the table above
- **AND** no English auto-generated label (e.g. "Global send interval minutes") is visible

### Requirement: Spanish verbose names on EmailTemplate fields
All fields of `EmailTemplate` (`apps/mailing/models.py`) SHALL declare an
explicit `verbose_name` in Spanish.

| Field | verbose_name |
|---|---|
| `name` | `"Nombre"` |
| `subject` | `"Asunto"` |
| `body_html` | `"Cuerpo HTML"` |
| `is_active` | `"Activa"` |
| `created_at` | `"Creada el"` |

#### Scenario: EmailTemplate change form shows Spanish labels
- **WHEN** a staff user opens `/admin/mailing/emailtemplate/<id>/change/`
- **THEN** each field label matches the Spanish string from the table above

### Requirement: Spanish verbose names on MailingLog fields
All fields of `MailingLog` (`apps/mailing/models.py`) SHALL declare an
explicit `verbose_name` in Spanish.

| Field | verbose_name |
|---|---|
| `user` | `"Usuario"` |
| `company` | `"Empresa"` |
| `email_template` | `"Plantilla de email"` |
| `cv` | `"CV"` |
| `cv_download_token` | `"Token de descarga del CV"` |
| `unsubscribe_token` | `"Token de baja"` |
| `sent_at` | `"Enviado el"` |
| `status` | `"Estado"` |
| `error_message` | `"Mensaje de error"` |
| `company_email_snapshot` | `"Email de la empresa"` |
| `unsubscribed_at` | `"Fecha de baja"` |

#### Scenario: MailingLog change form shows Spanish labels
- **WHEN** a staff user opens `/admin/mailing/mailinglog/<id>/change/`
- **THEN** each field label matches the Spanish string from the table above

### Requirement: SystemSettingsAdmin fieldset descriptions are pure Spanish prose
`SystemSettingsAdmin` (`apps/mailing/admin.py`) SHALL NOT expose raw Python identifier names in its fieldset `description` strings. Both descriptions MUST be rewritten as fully Spanish prose that explains the effect of the fields without referencing their Python names.

#### Scenario: Fieldset description contains no Python identifiers
- **WHEN** a staff user opens `/admin/mailing/systemsettings/1/change/`
- **THEN** neither fieldset description contains a string matching
  `global_send_interval_minutes`, `company_cooldown_hours`,
  `max_emails_per_day_per_user`, `initial_free_credits`,
  or `hidden_credit_multiplier`
- **AND** both descriptions are written entirely in Spanish

### Requirement: EmailTemplate admin preview column label is Spanish
`EmailTemplateAdmin` (`apps/mailing/admin.py`) SHALL set `preview_link.short_description` to `"Vista previa"` instead of the English `"Preview"`.

#### Scenario: EmailTemplate changelist column header reads "Vista previa"
- **WHEN** a staff user opens `/admin/mailing/emailtemplate/`
- **THEN** the column header for the preview link reads `"Vista previa"`
- **AND** the previous English header `"Preview"` is not visible
