## 1. Models & Database
- [x] 1.1 Update `apps/mailing/models.py`: Add `initial_free_credits` and `hidden_credit_multiplier` to `SystemSettings`.
- [x] 1.2 Update `apps/accounts/models.py`: Add `total_purchased_credits` to `User`.
- [x] 1.3 Update `apps/accounts/models.py`: Add `visible_credits` property to `User`.
- [x] 1.4 Generate and run migrations: `python manage.py makemigrations` and `python manage.py migrate`.
- [x] 1.5 Create data migration to populate `total_purchased_credits` for existing users from `StripePayment`.

## 2. Logic Implementation
- [x] 2.1 Update `apps/accounts/signals.py`: Modify `grant_signup_bonus` to use `SystemSettings.get().initial_free_credits`.
- [x] 2.2 Update `apps/payments/views.py`: In `_handle_successful_payment`, increment `total_purchased_credits` and adjust `credits_remaining` increment to "forgive" negative balances.
- [x] 2.3 Update `apps/mailing/tasks.py`: Refactor `process_mailing_queue` to include the hidden multiplier in the user eligibility check.

## 3. UI & Templates
- [x] 3.1 Update `templates/base.html`: Use `user.visible_credits` in the navbar chip.
- [x] 3.2 Update `templates/dashboard/index.html`: Use `user.visible_credits` in the stat card.
- [x] 3.3 Update `apps/dashboard/views.py`: Ensure flash messages and logic (e.g., `toggle_campaign`) use the correct visibility/eligibility checks.

## 4. Verification
- [x] 4.1 Add unit tests for `grant_signup_bonus` with dynamic settings.
- [x] 4.2 Add unit tests for `_handle_successful_payment` with negative balance forgiveness.
- [x] 4.3 Add integration tests for `process_mailing_queue` verifying the hidden multiplier threshold.
- [x] 4.4 Verify UI correctly clamps negative balances to zero.
