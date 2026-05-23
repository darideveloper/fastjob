# Change: Update pricing card copy and add configurable sends floor

## Why
Two small trust-signal improvements are needed on the pricing page:
1. The feature-list label reads `CVs enviados` but should be `CVs enviados exitosamente` to communicate successful delivery rather than bare volume.
2. The platform-wide sends counter shows the real database count, which is zero on fresh installs — admins need a configurable floor value so the page always projects credibility.

## What Changes
- `templates/payments/packages.html`: change the per-card feature label from `CVs enviados` to `CVs enviados exitosamente`.
- `templates/payments/packages.html`: remove the per-card trust signal badge (`✓ +N envíos exitosos en la plataforma`) from inside each card; the trust signal is shown **only** in the page-level footer bar.
- `apps/mailing/models.py` → `SystemSettings`: add integer field `displayed_sends_floor` (default `0`, non-negative) configurable from `/admin/mailing/systemsettings/`.
- `apps/mailing/admin.py` → `SystemSettingsAdmin`: add a new "Página de Paquetes" fieldset exposing `displayed_sends_floor` so it appears in the admin change form.
- `apps/payments/views.py` → `packages()`: compute `successful_sends_count` as `max(real_count, SystemSettings.get().displayed_sends_floor)`. The trust signal continues to be hidden when this computed value is zero.
- One Django migration adding the new `SystemSettings` field.

## Impact
- Affected specs: `pricing`, `mailing`
- Affected code:
  - `templates/payments/packages.html`
  - `apps/payments/views.py`
  - `apps/mailing/models.py`
  - `apps/mailing/admin.py`
  - New migration in `apps/mailing/migrations/`
- No URL, model rename, or breaking changes.
