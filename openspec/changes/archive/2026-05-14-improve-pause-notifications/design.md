# Design: Dynamic Pause Notifications and UI Feedback

## Architectural Reasoning

### State Persistence for Pause Reason
To provide UI feedback, the reason for the campaign pause must be persisted. We will add a `campaign_pause_reason` field to the `User` model.
- **Field**: `campaign_pause_reason = models.CharField(max_length=20, blank=True)`
- **Values**:
    - `expired`: Token or session issue.
    - `quota`: Provider daily limit reached.
    - `unlinked`: OAuth account disconnected by user.
    - `""` (Empty): Manual pause or active campaign.

### UI Banner Component
We will add a conditional block at the top of the dashboard content. If `user.campaign_pause_reason` is set, we display a styled banner (e.g., yellow for quota, red for expired/unlinked) with a clear explanation and call to action.

### Automated Clearing
The `campaign_pause_reason` should be cleared whenever the user takes an explicit action to manage their campaign (Start/Stop). This prevents old, stale warnings from persisting after the user has addressed the issue.

### Notification Refactoring
The email notification task will now be the secondary channel, mirroring the information shown in the UI.

**Email Mapping:**
- `reason='expired'`: Subject: "FastJob: Vuelve a conectar tu cuenta de correo"
- `reason='quota'`: Subject: "FastJob: Límite diario de tu proveedor alcanzado"
- `reason='unlinked'`: (No email needed as the user initiated the unlink, but the field helps the dashboard explain why it's paused).

### Provider-Specific Detection
- **Microsoft Graph**: Look for `ErrorExceededMessageLimit`.
- **Gmail**: Look for `rateLimitExceeded`, `userRateLimitExceeded`, or `(Mail sending)`.

## Trade-offs
- **Model Bloat**: Adding a field to `User` for UX state is a trade-off against keep models lean, but since `User` is the central aggregate for campaigns, it's the most reliable place to store this cross-app state.
