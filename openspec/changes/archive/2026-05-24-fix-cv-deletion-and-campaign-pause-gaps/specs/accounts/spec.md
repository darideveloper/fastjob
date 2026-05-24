## ADDED Requirements

### Requirement: OAuth Unlink Signal Sends Notification

The `pause_campaign_on_unlink` signal handler in `apps/accounts/signals.py` MUST enqueue `send_campaign_paused_notification.delay(user.pk, "unlinked")` after setting `is_campaign_active = False` and `campaign_pause_reason = "unlinked"`, so that users who disconnect their OAuth account receive an explanatory email. This matches the notification pattern used by the `TokenExpiredError` and `QuotaExceededError` handlers in `process_mailing_queue`.

#### Scenario: Disconnecting OAuth account triggers notification email

- **GIVEN** a user with an active campaign and a linked OAuth account
- **WHEN** the user disconnects their OAuth account (triggering `social_account_removed`)
- **THEN** `is_campaign_active` is set to `False`
- **AND** `campaign_pause_reason` is set to `"unlinked"`
- **AND** `send_campaign_paused_notification.delay(user.pk, "unlinked")` is enqueued
- **AND** the user receives an email explaining that their email account was disconnected and providing a link to re-link

## MODIFIED Requirements

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

The `campaign_pause_reason` field accepts the following values:
`""` (empty, no pause), `"quota"`, `"expired"`, `"unlinked"`, and `"missing_cv"`.

#### Scenario: User change form shows Spanish labels for FastJob fields

- **WHEN** a staff user opens `/admin/accounts/user/<id>/change/`
- **THEN** the FastJob fieldset labels for the five fields above match
  their Spanish verbose names
- **AND** no English auto-generated label is visible