# Design: Hardening the Mailing Engine

## Architectural Reasoning

### Status-Agnostic Cooldowns
The current implementation of `process_mailing_queue` only considers `MailingLog` entries with `status='sent'` when determining if a user is eligible for their next "slow-drip" send. 
```python
# current logic
last_log = MailingLog.objects.filter(user=user, status=SENT).order_by("-sent_at").first()
```
If a send fails (e.g., due to a temporary network error or a 429 rate limit), no `SENT` log is created. On the next task tick (1 minute later), the system sees the same "last successful send" and attempts another delivery. This creates a feedback loop where failures accelerate the retry frequency, exactly when the system should be backing off.

**Decision**: The interval check will now be based on the last *attempt* (any status). This preserves the "human-like" delivery rhythm regardless of outcome and prevents overwhelming third-party APIs during outages.

### Multi-Phase Error Classification
Errors in OAuth integrations occur at two distinct phases: **Refresh** and **Send**.
1.  **Refresh Phase**: Already well-classified in `engine.py` (Transient vs. Terminal).
2.  **Send Phase**: Currently unclassified.

By applying the same classification logic to the Send phase (HTTP 401/403 -> Terminal; HTTP 429/5xx -> Transient), we ensure that:
-   A user whose token was revoked during the day is paused immediately (Terminal).
-   A user hitting a temporary throttle is skipped for 5 minutes (Transient + New Interval Logic).

### Expiry Buffer Tuning
Microsoft tokens typically last 60-90 minutes. A 1-minute buffer is extremely tight. If the server clock drifts by 61 seconds, we use a stale token. A 10-minute buffer (600s) provides a healthy margin for error without significantly increasing the number of refresh calls.

## Trade-offs
-   **Aggressive Pausing**: By treating 401s during Send as terminal, we might pause a campaign for a transient 401 (if Microsoft has a temporary bug). However, this is safer than allowing a broken integration to churn through logs.
-   **Lower Throughput on Failure**: If an email fails for a non-transient reason (e.g., malformed template), the user will now wait 5 minutes between failures instead of 1. This is a deliberate "safe-by-default" choice.
