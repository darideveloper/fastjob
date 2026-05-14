## ADDED Requirements

### Requirement: Track Lifetime Purchased Credits
The `User` model MUST track the lifetime total of credits purchased via Stripe to support multiplier-based limits.
- This field `total_purchased_credits` MUST be updated whenever a `StripePayment` reaches `COMPLETED` status.
- It MUST NOT include free signup bonuses or manual adjustments.

#### Scenario: Payment completion increments lifetime total
- **GIVEN** a user with `total_purchased_credits = 50`.
- **WHEN** a new payment for 100 credits is completed.
- **THEN** `total_purchased_credits` MUST be updated to `150`.

### Requirement: Visible Credit Balance
The `User` model MUST provide a sanitized credit balance for UI display that hides negative values resulting from the hidden multiplier.
- The property `visible_credits` MUST return `max(0, credits_remaining)`.
- All public-facing dashboard and navbar elements MUST use this property instead of the raw `credits_remaining`.

#### Scenario: Negative balance is hidden in UI
- **GIVEN** a user with `credits_remaining = -3`.
- **WHEN** the `visible_credits` property is accessed.
- **THEN** it MUST return `0`.
