## Why

Currently, clients buy email credits through Stripe, and their payment/purchase history is stored in the database. However, this history is only visible to administrators in the Django Admin. Showing this information to the clients in their dashboard increases transparency, allows them to track their spending, and provides a quick access link to Stripe Billing Portal to download invoices and receipts.

## What Changes

- Modify the client dashboard view to retrieve and include the logged-in user's payment history (`StripePayment` instances).
- Add a new "Historial de compras" section at the bottom of the client dashboard template (`index.html`) using Tailwind CSS.
- Display each purchase concept, credits granted, amount paid, transaction date/time, and status (with badges).
- Integrate a button to redirect the user to Stripe's hosted Billing Portal for downloading invoices.
- Add a descriptive empty state when no purchases have been recorded.
- Fix a pre-existing `NoReverseMatch` bug in error handler tests by adding dummy routes for `privacy` and `terms` in the test URLconf.

## Capabilities

### New Capabilities
- `payment-history`: Display Stripe credit purchase records and invoice download access for users.

### Modified Capabilities
- `dashboard`: Integrate the payment history panel into the existing main user dashboard page.

## Impact

- **Views:** Modifies `apps/dashboard/views.py` to query and pass user payment history.
- **Templates:** Updates `templates/dashboard/index.html` to render the payment history section.
- **Tests:** Fixes URLconf references in `config/tests/test_error_handlers.py`.
