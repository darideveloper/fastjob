## 1. Clean Up Dashboard Template and View

- [x] 1.1 Remove the form button for Stripe billing portal redirection from the "Historial de compras" section header in `templates/dashboard/index.html`.
- [x] 1.2 Remove the calculation of `has_completed_payments` and its inclusion in the context map in `apps/dashboard/views.py`.

## 2. Update Unit Tests

- [x] 2.1 Edit `test_dashboard_displays_payment_history` in `apps/dashboard/tests/test_dashboard.py` to remove assertions checking for the presence of the text `"Facturación y Recibos (Stripe)"`.

## 3. Verification

- [x] 3.1 Run `.venv/bin/pytest` to ensure all tests pass successfully.
