## Context
The project uses a simple `credits_remaining` integer on the `User` model. We need to introduce more flexible signup rewards and a safety margin for paid users without confusing them with complex balance calculations in the UI.

## Goals
- Allow admin to change initial credits without code deployment.
- Grant paid users ~10% (configurable) extra sends "hidden" from the UI.
- Ensure re-purchasing doesn't feel like "paying back" the hidden debt.

## Decisions

### 1. Dynamic Signup Bonus
**Decision**: Add `initial_free_credits` to the `SystemSettings` singleton.
**Rationale**: It keeps the configuration centralized alongside other mailing limits like the daily cap.

### 2. Hidden Multiplier and Negative Balance
**Decision**: Allow `credits_remaining` to go negative, supported by a `total_purchased_credits` tracking field.
**Rationale**: 
- Using `credits_remaining` as the source of truth for "sends remaining vs paid" is simpler than tracking "sends made".
- By allowing negative values, the mailing engine can simply check if the value is above a floor.
- **Formula**: `extra_limit = ceil(user.total_purchased_credits * (multiplier - 1))`
- **Eligibility**: `user.credits_remaining > -extra_limit`

### 3. UI Clamping
**Decision**: Implement a `visible_credits` property on the `User` model.
**Rationale**: This ensures that even if a user is at `-3` (using their hidden margin), the UI shows `0`. This maintains the illusion of the "hidden" limit.

### 4. Credit Refill Logic (Forgiveness)
**Decision**: When a purchase occurs, if the balance is negative, we add `package.credits + abs(balance)`.
**Rationale**: If a user is at `-5` and buys `50`, simply adding `50` would result in `45`. The user expects `50`. By adding `55`, we reset them to exactly `50`, essentially forgiving the extra credits they used.

## Risks / Trade-offs
- **Data Integrity**: `total_purchased_credits` must be updated atomically alongside `credits_remaining` during Stripe webhooks.
- **Multiplier Changes**: If the multiplier is decreased, some users might find their campaigns paused if their current negative balance is now deeper than the new floor. This is an edge case but expected behavior.
- **Refunds**: If a payment is refunded, we should technically decrement `total_purchased_credits`, though this is not explicitly requested yet.

## Migration Plan
1. Add new fields to `User` and `SystemSettings`.
2. Data Migration: Set `total_purchased_credits` for existing users by summing their `COMPLETED` StripePayment records.
3. Code deployment.
