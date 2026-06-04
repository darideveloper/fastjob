## 1. Backend View Integration

- [x] 1.1 Query `StripePayment` instances for the logged-in user in `apps/dashboard/views.py`.
- [x] 1.2 Optimize query using `select_related('package')` to avoid N+1 query patterns.
- [x] 1.3 Add query results to the template context of the `index` view.

## 2. Frontend UI Update

- [x] 2.1 Append a new payment history section at the bottom of `templates/dashboard/index.html`.
- [x] 2.2 Design a responsive table using Tailwind CSS for Concept, Credits, Amount, Date, and Status.
- [x] 2.3 Add semantic color badges for payment statuses (Completado, Pendiente, Fallido).
- [x] 2.4 Integrate a Stripe Billing Portal redirection button inside the section header.
- [x] 2.5 Style an empty state layout for users with no payment history.

## 3. Test Suite Fixes

- [x] 3.1 Define placeholder routes for `privacy` and `terms` inside the test URLconf in `config/tests/test_error_handlers.py`.
- [x] 3.2 Verify all tests pass by running `.venv/bin/pytest`.
