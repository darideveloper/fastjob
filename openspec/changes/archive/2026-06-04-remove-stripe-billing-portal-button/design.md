## Context

Currently, the client dashboard renders a "Facturación y Recibos (Stripe)" button at the bottom under the "Historial de compras" section. However, the stats card at the top of the page already includes a "Facturación" button linking to the same Stripe Billing Portal. Since having multiple buttons linking to the same resource in close proximity on the same dashboard is redundant, we are removing the bottom button.

## Goals / Non-Goals

**Goals:**
* Remove the Stripe Billing Portal redirection button inside the "Historial de compras" section header.
* Keep the dashboard view clean by removing unnecessary context variables (`has_completed_payments`).
* Update unit tests that check for the presence of the "Facturación y Recibos (Stripe)" button text in the response content.

**Non-Goals:**
* Removing the "Facturación" link in the top "Envíos disponibles" stats card.
* Disabling the Stripe Customer Billing Portal view or API logic.

## Decisions

### 1. Simplify Context Variables in Dashboard View
* **Decision:** Completely remove `has_completed_payments` from the dashboard view context.
* **Rationale:** Since the bottom button was the only element relying on this boolean variable, removing it keeps the view simple and avoids calculating/passing unused data.
* **Alternatives considered:** Keeping the variable in context. Rejected because unused context variables clutter code and make future refactoring harder.

## Risks / Trade-offs

* **Risk:** The user might find it slightly harder to locate the billing portal if they look for it specifically under the payments section.
* **Mitigation:** The "Facturación" link is prominently displayed in the "Envíos disponibles" card at the top of the dashboard, which is the standard place for managing account credits and invoicing.
