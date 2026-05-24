## Context

FastJob's slow-drip mailing engine sends CV PDFs on behalf of users. The current code has interconnected gaps that cause silent campaign pauses with no user feedback, plus a missing server-side guard on CV deletion during active campaigns.

### Current behaviour (broken)

| Scenario | What happens | User feedback |
|----------|-------------|---------------|
| Delete any CV, campaign active | CV deleted; if last CV, campaign auto-pauses with `campaign_pause_reason = ""`; if other CVs exist, `active_cv` silently switches | No banner, no email |
| Direct POST to delete CV during active campaign | CV deleted, campaign may auto-pause | No guard |
| S3 file disappears, engine sends | Engine sets `is_campaign_active = False` but not `campaign_pause_reason`; raises generic `Exception` | No banner, no email |
| OAuth account disconnected | Campaign paused with `campaign_pause_reason = "unlinked"` | Banner visible, but **no notification email** |

### Desired behaviour

| Scenario | What should happen | User feedback |
|----------|-------------------|---------------|
| Try to delete any CV, campaign active | Server rejects the deletion | Flash error + hidden button |
| S3 file disappears, engine sends | `CVFileMissingError` raised; task pauses campaign with `campaign_pause_reason = "missing_cv"` and enqueues notification | Banner + email |
| OAuth account disconnected | Campaign paused with `campaign_pause_reason = "unlinked"` and notification sent | Banner + email |

## Goals / Non-Goals

- **Goals**: Prevent silent campaign pauses; give users clear feedback at every pause point; block CV deletion during active campaigns at both template and server level; follow the existing typed-exception + task-level-pause pattern.
- **Non-Goals**: Resume/pause campaigns automatically when CVs are re-uploaded (future enhancement); change the `cv_download` token-based flow; modify the admin CV deletion path (admin users are staff).

## Decisions

### 1. Block deletion at both template and server level

- **Template**: Hide the "Eliminar" button on all CV rows when `user.is_campaign_active`.
- **Server**: `delete_cv` returns an error message if `user.is_campaign_active`, even if bypassed via direct POST.
- **Rationale**: Defense in depth. The template is UX-friendly (no confusing button); the server guard prevents API bypass. The server message is the authoritative source.

### 2. New pause reason: `missing_cv`

- **Value**: `"missing_cv"` added alongside `"quota"`, `"expired"`, `"unlinked"`.
- **Rationale**: A distinct reason lets the dashboard show targeted copy ("Tu archivo CV no está disponible — sube un nuevo CV para continuar") and lets the notification email point to the right action.
- **Migration**: No schema migration needed — `campaign_pause_reason` is already `CharField(max_length=20, blank=True)`. `"missing_cv"` fits within 20 chars.

### 3. Typed exception for CV read failures

- **Pattern**: Define `CVFileMissingError` in `engine.py` alongside the existing `TokenExpiredError`, `QuotaExceededError`, and `TokenRefreshTransientError`.
- **Engine behaviour**: Remove `is_campaign_active = False` and `save()` from the engine's CV-read except block. Instead, simply raise `CVFileMissingError`. This aligns with how `TokenExpiredError` and `QuotaExceededError` work — the engine raises, the task pauses.
- **Task behaviour**: Add `except CVFileMissingError` handler in `process_mailing_queue` that sets both `is_campaign_active = False` and `campaign_pause_reason = "missing_cv"`, then enqueues `send_campaign_paused_notification.delay(user.pk, "missing_cv")` — identical in structure to the `TokenExpiredError` and `QuotaExceededError` handlers.

### 4. Fill `unlinked` notification gap

- **Current**: Two problems compound: (a) `send_campaign_paused_notification` has an `else` branch that silently returns without sending an email for `reason="unlinked"`, and (b) the `pause_campaign_on_unlink` signal handler in `apps/accounts/signals.py` never calls `send_campaign_paused_notification.delay()` at all — so even adding an `unlinked` branch would have no effect without also invoking it.
- **Fix**: Add a dedicated `elif reason == "unlinked"` branch with a Spanish email explaining the account was disconnected and providing a re-link URL. Add `send_campaign_paused_notification.delay(user.pk, "unlinked")` to the `pause_campaign_on_unlink` signal handler, matching how the task enqueues notifications for `"expired"` and `"quota"`.

### 5. CV deletion rejection message (Spanish)

- Flash message: `"Para eliminar un CV, primero pausa tu campaña."` — clear, actionable.

## Risks / Trade-offs

- **Risk**: Users with only one CV who want to replace it must now: pause campaign → delete CV → upload new CV → restart campaign. This is intentionally more explicit than the current silent behaviour.
- **Risk**: The `"missing_cv"` pause reason could trigger if S3 has a transient outage that manifests as `OSError`. Mitigation: the env catches `OSError`, but genuine S3 outages usually surface as HTTP errors at the send stage (not file-read stage). The `FileNotFoundError` and `ValueError` catches are more specific indicators that the file reference is invalid.

## Open Questions

-none-