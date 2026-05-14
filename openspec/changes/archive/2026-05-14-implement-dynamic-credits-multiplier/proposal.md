# Change: Implement Dynamic Credits and Hidden Multiplier

## Why
Currently, the signup bonus is hardcoded, preventing easy marketing adjustments. Additionally, we want to provide a "hidden" safety margin (extra credits) to paid users to improve customer satisfaction and reduce campaign pauses due to exact zero balances, while keeping the UI clean and simple.

## What Changes
- **Dynamic Signup Bonus**: Moves the hardcoded 5-credit signup bonus to a configurable field in `SystemSettings`.
- **Hidden Credit Multiplier**: 
    - Adds a `hidden_credit_multiplier` (e.g., 1.1) to `SystemSettings`.
    - Tracks `total_purchased_credits` on the `User` model to calculate the extra margin.
    - Updates the mailing engine to allow sending as long as `credits_remaining > -extra_limit`.
    - **UI Transparency**: Dashboard and Navbar continue to show only the "paid" credits (clamped to 0).
    - **Negative Balance Forgiveness**: When a user with a negative balance (using their hidden margin) buys a new package, the purchased credits are added such that the final balance equals the purchased amount (forgiving the "extra" they already used).

## Impact
- **Affected Specs**: `mailing`, `accounts`, `dashboard`, `pricing`
- **Affected Code**:
    - `apps/mailing/models.py` (SystemSettings updates)
    - `apps/mailing/tasks.py` (Mailing engine check)
    - `apps/accounts/models.py` (User model updates)
    - `apps/accounts/signals.py` (Dynamic bonus)
    - `apps/payments/views.py` (Refill logic)
    - `templates/dashboard/index.html` (UI clamping)
    - `templates/base.html` (Navbar clamping)
