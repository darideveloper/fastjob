## ADDED Requirements

### Requirement: Spanish verbose names on StripePayment fields
All fields of `StripePayment` (`apps/payments/models.py`) SHALL declare
an explicit `verbose_name` in Spanish.

| Field | verbose_name |
|---|---|
| `user` | `"Usuario"` |
| `package` | `"Paquete"` |
| `stripe_session_id` | `"ID de sesión Stripe"` |
| `stripe_payment_intent` | `"Payment intent Stripe"` |
| `amount_eur` | `"Importe (€)"` |
| `credits_granted` | `"Envíos otorgados"` |
| `status` | `"Estado"` |
| `created_at` | `"Creado el"` |
| `completed_at` | `"Completado el"` |

`stripe_session_id` and `stripe_payment_intent` are internal Stripe
identifiers that must stay unique and searchable; only their displayed
labels are translated.

#### Scenario: StripePayment change form shows Spanish field labels
- **WHEN** a staff user opens `/admin/payments/stripepayment/<id>/change/`
- **THEN** each field label matches the Spanish string from the table above
- **AND** no English auto-generated label (e.g. "Stripe session id",
  "Credits granted", "Completed at") is visible

### Requirement: Spanish verbose name on SystemConfig field
`SystemConfig` (`apps/core/models.py`) SHALL declare `verbose_name="Guardar en carpeta Enviados"` on the `save_emails_to_sent_folder` field, and its `help_text` SHALL be entirely in Spanish with no English words embedded.

#### Scenario: SystemConfig change form shows Spanish label and help text
- **WHEN** a staff user opens `/admin/core/systemconfig/1/change/`
- **THEN** the field label reads `"Guardar en carpeta Enviados"`
- **AND** the help text contains no English words
