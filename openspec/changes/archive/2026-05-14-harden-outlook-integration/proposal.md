# Proposal: Harden Outlook Integration and Mailing Engine

## Why
The current Outlook integration and mailing engine suffer from several robustness issues in production:
1.  **Short Token Lifespan & Clock Skew**: Tokens are refreshed with a minimal 60-second safety buffer. Clock drift between the server and Microsoft often causes the system to use an expired token, resulting in `401 Unauthorized` errors.
2.  **Retry Storms**: The mailing engine only respects the `send_interval` (slow-drip) for successful sends (`status=SENT`). If a send fails, the engine re-attempts every minute, potentially leading to rate-limiting and API abuse.
3.  **Missing Error Classification**: Authentication errors during the sending phase (HTTP 401) are caught as generic exceptions. This prevents the system from automatically pausing the campaign when a token truly expires or is revoked.
4.  **Inadequate Rate Limit Handling**: HTTP 429 (Too Many Requests) from Microsoft Graph is treated as a hard failure instead of a transient one, causing unnecessary log noise and potential campaign issues.

## Proposed Changes
### 0. Azure Configuration (External Dependency)
- **Token Lifetime Policy**: A custom `TokenLifetimePolicy` has already been applied to the `fastjob` Service Principal via PowerShell, increasing the `AccessTokenLifetime` to 24 hours (23:59:59). The codebase changes below are designed to leverage this longer lifetime securely.

### 1. Mailing Engine (`apps/mailing/engine.py`)
- **Increase Refresh Buffer**: Change the "cheap path" expiry check from 60 seconds to 10 minutes (600 seconds) to tolerate clock skew and intermittent refresh delays.
- **Improve Error Classification**: 
    - Update `_send_via_microsoft` to check the response status code.
    - Map `401 Unauthorized` and `403 Forbidden` to `TokenExpiredError` (to trigger campaign pause).
    - Map `429 Too Many Requests` and `5xx` to `TokenRefreshTransientError` (to trigger a skip without pause).

### 2. Mailing Tasks (`apps/mailing/tasks.py`)
- **Status-Agnostic Cooldown**: Modify `process_mailing_queue` to check the `last_log` timestamp regardless of its `status`. This ensures the system waits the full `send_interval` even after a failure, preventing retry storms.

## Impact
- **Stability**: Reduces the frequency of "Account Disconnected" events caused by minor clock drift.
- **Resilience**: Prevents aggressive minute-by-minute retries that can lead to IP blocks or account suspensions.
- **User Experience**: Automatically pauses campaigns when action is required (e.g., re-link needed) while silently handling transient API blips.
