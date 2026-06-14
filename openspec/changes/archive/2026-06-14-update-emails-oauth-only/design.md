## Context

FastJob users only register and authenticate via Google or Microsoft OAuth. Standard username/password logic, connections screens, and unlinking views are unmounted. Because of this, certain onboarding instructions are misleading, and certain pause reasons are confusingly worded.

## Goals / Non-Goals

**Goals:**
- Align `welcome` email templates with OAuth-only signup flow by removing instructions to link accounts.
- Align `campaign_paused` email templates with the authentication constraints by rewording "expired token" notification to clearly suggest re-logging in.
- Disable/remove the redundant "OAuth linked" confirmation email upon user registration.

**Non-Goals:**
- Modifying the login/signup authentication flow itself.
- Re-enabling password reset or manual linking views.

## Decisions

### 1. Simplify Welcome Email
- **Decision:** Remove the `Vincular tu cuenta de Google o Microsoft` step from `welcome.html` and `welcome.txt` templates.
- **Rationale:** The user is already registered via OAuth, so their social account is already linked. 

### 2. Clarify Campaign Paused Email
- **Decision:** Reword the `expired` condition in `campaign_paused_notification.html` and `campaign_paused_notification.txt` to state that the email session/connection has expired, advising them to log in again.
- **Rationale:** The current wording "ha caducado" implies the campaign itself has expired, causing confusion.

### 3. Disable Redundant OAuth Linked Email
- **Decision:** Disconnect/remove the `@receiver(social_account_added)` signal handler (`notify_oauth_link`) in `apps/accounts/signals.py` and delete/clean up the corresponding unit tests in `apps/accounts/tests/test_oauth_email.py`.
- **Rationale:** Since manual account linking is disabled in the UI, this email is redundant with the onboarding welcome email.

## Risks / Trade-offs

- **[Risk]**: Disabling `social_account_added` signal might break existing tests that assert its behavior.
  - *Mitigation*: Delete or update tests in `apps/accounts/tests/test_oauth_email.py` that rely on `send_oauth_link_email` and `notify_oauth_link`.
