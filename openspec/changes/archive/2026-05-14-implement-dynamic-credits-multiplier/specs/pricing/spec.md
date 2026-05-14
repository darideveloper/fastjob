## ADDED Requirements

### Requirement: Negative Balance Forgiveness on Purchase
When a user with a negative credit balance (due to the hidden multiplier margin) purchases a new credit package, the system MUST "forgive" the debt so that their final balance matches the purchased quantity.
- The amount added to `credits_remaining` MUST be `package.credits + abs(min(0, user.credits_remaining))`.

#### Scenario: User at -5 credits buys 50
- **GIVEN** a user with `credits_remaining = -5`.
- **WHEN** they complete a purchase for a package with 50 credits.
- **THEN** the system MUST add 55 credits to their balance.
- **AND** the final `credits_remaining` MUST be `50`.
