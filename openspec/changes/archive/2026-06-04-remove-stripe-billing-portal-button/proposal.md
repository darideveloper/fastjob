## Why

The "Facturación y Recibos (Stripe)" button was recently added to the bottom "Historial de compras" section header on the dashboard. However, having this button is redundant as there is already a "Facturación" link inside the "Envíos disponibles" stat card at the top. Removing this button simplifies the dashboard UI and avoids multiple access points to the Stripe Billing Portal.

## What Changes

* Remove the "Facturación y Recibos (Stripe)" button from the header of the "Historial de compras" section in the client dashboard template (`index.html`).
* Remove the `has_completed_payments` context variable and its calculation from the dashboard view (`apps/dashboard/views.py`) if it's no longer needed elsewhere.
* Update unit tests to reflect the removal of this button.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
* `payment-history`: Remove the requirement for the Stripe Billing Portal integration button inside the payment history section.

## Impact

* **Views:** Modifies `apps/dashboard/views.py` to remove `has_completed_payments` from context.
* **Templates:** Modifies `templates/dashboard/index.html` to remove the button form.
* **Specs:** Modifies `openspec/specs/payment-history/spec.md` to remove the Billing Portal button requirement.
* **Tests:** Modifies `apps/dashboard/tests/test_dashboard.py` to remove assertions checks for "Facturación y Recibos (Stripe)".
