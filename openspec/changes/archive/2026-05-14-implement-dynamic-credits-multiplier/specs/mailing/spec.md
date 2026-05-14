## ADDED Requirements

### Requirement: Dynamic Initial Credits
The system SHALL allow the administrator to configure the number of free credits granted to new users upon signup. This value MUST be stored in the `SystemSettings` singleton as `initial_free_credits` and default to 5.

#### Scenario: New user receives dynamic signup bonus
- **GIVEN** `SystemSettings.initial_free_credits` is set to 10.
- **WHEN** a new user signs up and the `user_signed_up` signal fires.
- **THEN** the user's `credits_remaining` MUST be set to 10.
- **AND** `total_purchased_credits` MUST remain at 0.

### Requirement: Hidden Credit Multiplier
The mailing engine SHALL allow paid users to send a small margin of extra emails beyond their purchased balance, controlled by a global multiplier.
- The multiplier `hidden_credit_multiplier` (e.g., 1.1 for 10% extra) is stored in `SystemSettings` and defaults to 1.00.
- The multiplier MUST only apply to `total_purchased_credits`, not to free signup bonuses.
- The "Hidden Floor" is calculated as `ceil(user.total_purchased_credits * (multiplier - 1))`.
- A user is eligible to send if `user.credits_remaining > -hidden_floor`.
- The `User.can_send()` method MUST be updated to incorporate this hidden floor check.

#### Scenario: User with 1.1x multiplier sends beyond zero
- **GIVEN** a user has purchased 50 credits (`total_purchased_credits = 50`).
- **AND** the global `hidden_credit_multiplier` is `1.1`.
- **AND** the user's `credits_remaining` is `0`.
- **WHEN** the mailing engine evaluates the user via `can_send()`.
- **THEN** it MUST return `True` because `0 > -ceil(50 * 0.1)` (which is `0 > -5`).
- **AND** the engine sends the email and decrements `credits_remaining` to `-1`.

#### Scenario: User hits the hidden floor
- **GIVEN** a user has purchased 50 credits and the multiplier is `1.1` (floor is `-5`).
- **AND** the user's `credits_remaining` is `-5`.
- **WHEN** the mailing engine evaluates the user via `can_send()`.
- **THEN** it MUST return `False` because `-5` is not greater than `-5`.

#### Scenario: Multiplier of 1.0 does not grant extra credits
- **GIVEN** a user has purchased 100 credits and the multiplier is `1.0`.
- **AND** the user's `credits_remaining` is `0`.
- **WHEN** the mailing engine evaluates the user.
- **THEN** it MUST return `False` because the floor is 0.
