## Context

FastJob sends two categories of email today:

1. **CV outbound emails** — rendered from `EmailTemplate.body_html` (raw inline-styled HTML stored in DB). These go through `_send_via_gmail()` and `_send_via_microsoft()` in the mailing engine. They contain `{company_name}` and `{unsubscribe_url}` placeholders but no shared layout, logo, or branding.

2. **Campaign-paused notifications** — plain text via `send_mail()` in `apps/mailing/tasks.py`. No HTML, no logo, no styling.

All system/notification emails are missing (welcome, payment receipt, low credits, account deletion confirmation, OAuth link confirmation).

Follows OpenSpec convention: this change spans multiple capabilities (mailing, accounts, pricing) so `design.md` is warranted.

## Goals

- Every email FastJob sends (system or campaign) has a shared branded layout with logo, brand colors, and footer.
- All missing system/notification emails are implemented as Celery tasks.
- Campaign-paused notifications are upgraded from plain text to HTML with the branded layout.
- CV outbound emails are wrapped in the branded layout before sending.
- All new emails are written in Spanish (consistent with the existing `send_campaign_paused_notification` and UI language).
- Email branding is configurable via `SystemSettings` so admins can adjust logo, brand colors, and footer text without code changes.

## Non-Goals

- Transactional email service (SendGrid, Mailgun, etc.) — we continue using Django SMTP + the user's own OAuth for campaign emails.
- Email A/B testing or per-template layout variants.
- Marketing/bulk email infrastructure beyond the existing slow-drip engine.
- Modifying the allauth email verification flow (`ACCOUNT_EMAIL_VERIFICATION = "none"` stays).

## Decisions

### D1: Shared email layout via Django template, not stored in DB

**Decision**: Create `templates/email/base.html` as a Django template that renders a full HTML email with logo, header, content block, and footer. Use `EmailMultiAlternatives` with both `text_content` and `html_content`. The Python helper `render_branded_email()` lives in `apps/mailing/email.py` (not in templatetags — it's a utility function, not a template tag).

**Rationale**: Storing the layout in a Django template (not in `SystemSettings` or `EmailTemplate`) means:
- Version-controlled changes, easy to review in PRs.
- Tailwind-compatible (inline styles generated at template render time).
- No admin UI needed for layout changes (too risky — a bad edit breaks all emails).
- Brand colors and logo URL come from `SystemSettings`/settings for dynamic parts.
- The `render_branded_email()` utility is importable by any app (`apps.mailing.email.render_branded_email`) without the template-tag dance.

**Alternatives considered**:
- Store layout HTML in `SystemSettings` — rejected: too easy for an admin typo to break all emails; no version control.
- Use a 3rd-party email builder (MJML, Premailer) — rejected: adds build step; inline styles via Django template are sufficient.
- Put `render_branded_email` in `templatetags` — rejected: it's a Python helper, not a template filter/tag. Importing from `apps.mailing.email` is cleaner.

### D2: Logo served from remote URL

**Decision**: The branded email layout uses `<img src="https://raw.githubusercontent.com/darideveloper/fastjob/refs/heads/main/static/images/fastjob-logo.png">` as the `EMAIL_LOGO_URL` default. Admins can override this via `SystemSettings.email_logo_url`.

**Rationale**: Email clients cannot load local static assets (`/static/images/...`). The logo must be served from a publicly accessible URL. Using the GitHub raw URL as default avoids needing S3/CDN setup, but operators should override this via `SystemSettings` to point at their own CDN in production.

**Alternatives considered**:
- Embed logo as Base64 CID attachment — rejected: some email clients (Outlook) strip CID images; adds complexity to both Gmail and Graph send paths.
- Always use S3/CDN — rejected: requires infra setup; GitHub raw URL works as a zero-config default.

### D3: All system emails are Celery tasks (except deletion confirmation)

**Decision**: Every new notification email (welcome, payment receipt, low credits, OAuth link confirmation) is a `@shared_task` in the relevant app's `tasks.py`, consistent with the existing `send_campaign_paused_notification` pattern. The account deletion confirmation is sent **synchronously** (not via Celery) because the User record is destroyed immediately after — a Celery task would find no user to email.

**Rationale**: Celery tasks are non-blocking, retryable, and consistent with the existing pattern. Using `send_mail()` synchronously in request handlers risks 500s on SMTP timeouts.

**Signal choices**:
- `user_signed_up` (allauth): welcome email — fires once on genuine signup, not on every social login.
- `social_account_added` (allauth): OAuth link confirmation — fires only when a new SocialAccount is connected. This is the correct signal (not `post_save` on `SocialAccount`, which would fire on every save, not just creation).
- Webhook handler: payment receipt — enqueued after credit grant.
- `process_mailing_queue`: low-credits warning — triggered after credit decrement with atomic race guard.

### D4: `SystemSettings` gains `email_logo_url`, `email_brand_color`, `email_footer_text`, and `low_credits_threshold`

**Decision**: Add these fields to `SystemSettings` with sensible defaults. Migration is additive (no data loss).

| Field | Type | Default | Purpose |
|---|---|---|---|
| `email_logo_url` | `URLField` | GitHub raw URL | Logo image in email header |
| `email_brand_color` | `CharField(7)` | `#007BFF` | Primary brand hex color |
| `email_footer_text` | `TextField` | `"© 2026 FastJob..."` | Footer line |
| `low_credits_threshold` | `IntegerField` | `0` | Credits at/below which the warning fires (0 = only at zero) |

**Rationale**: `SystemSettings` is already the singleton config for the mailing engine. Adding email branding fields here avoids a new model. `low_credits_threshold = 0` means the warning fires only when credits hit zero, which is the current behavior (no email). Setting it to e.g. 5 means the email fires when credits drop to 5 or below.

### D5: Branded layout is injected after `EmailTemplate.render()`

**Decision**: The `send_cv_email` function calls `render_branded_email(body_html, subject)` after `template.render()` to wrap the campaign body in the shared layout. This keeps `EmailTemplate.body_html` as the user's content-only HTML and adds the chrome at send time.

**Rationale**: This is the simplest approach that doesn't require migration of existing templates. The DB-stored templates remain content-only; the wrapper is applied consistently.

### D6: Campaign-paused notifications use `EmailMultiAlternatives`

**Decision**: Replace `send_mail()` in `send_campaign_paused_notification` with `EmailMultiAlternatives` that includes both a plain-text and an HTML alternative rendered from the branded layout.

**Rationale**: `send_mail()` only sends plain text. Major email clients prefer HTML. Using `EmailMultiAlternatives` gives us both parts. The plain-text body is generated from the same context data.

### D7: Account deletion email is synchronous

**Decision**: The deletion confirmation email is sent **synchronously** in the `delete_account` view, before `user.delete()`. Not via Celery.

**Rationale**: After `user.delete()`, the user record no longer exists, so a Celery task cannot look up the email. Sending synchronously before delete ensures the address is available. If sending fails (SMTP timeout), we log a warning and proceed with deletion anyway — the email is best-effort, not a prerequisite for account removal.

**Alternatives considered**:
- Pass `user.email` to a Celery task, then delete — rejected: adds complexity; the email is a courtesy, not a transactional requirement.

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| Logo URL may break if GitHub repo is renamed or branch deleted | Document that production deployments should override `email_logo_url` to point at their own CDN. The GitHub URL is a dev/default only. |
| Inline CSS bloat in emails | Keep layout minimal — logo, one accent color, footer. No complex layouts. |
| Email client rendering variance | Use table-based layout for the header/footer (email-client safe), but content can be simple `<div>` blocks since the content is already inline-styled HTML from `EmailTemplate`. |
| Adding `SystemSettings` fields requires migration | Fields have defaults; migration is additive. No data loss. |
| Concurrent low-credits warning enqueues | Atomic `WHERE last_low_credits_warning_at IS NULL` update ensures only one warning per threshold crossing, even with parallel workers. |

## Migration Plan

1. Create `templates/email/base.html` and `base.txt` (shared layout templates).
2. Create `apps/mailing/email.py` with `render_branded_email()` helper.
3. Add `SystemSettings` fields via migration (four new fields with defaults).
4. Add `User.last_low_credits_warning_at` via migration (one new nullable field).
5. Create `apps/accounts/tasks.py` with `send_welcome_email` and `send_oauth_link_email` tasks.
6. Create `apps/payments/tasks.py` with `send_payment_receipt_email` task.
7. Create new email templates (welcome, receipt, low-credits, deletion confirmation, oauth linked).
8. Update `send_cv_email` to wrap rendered body in branded layout.
9. Update `send_campaign_paused_notification` to use `EmailMultiAlternatives` with branded layout.
10. Wire signals (`user_signed_up`, `social_account_added`, payment webhook) to dispatch new emails.
11. Update `process_mailing_queue` for low-credits warning with atomic race guard.
12. Update `_handle_successful_payment` to reset `last_low_credits_warning_at`.
13. Update `delete_account` to send deletion confirmation email synchronously.
14. Run tests; no existing behavior is removed, only enhanced.

## Open Questions

1. ~~**Should account deletion confirmation email be sent before or after the user record is destroyed?**~~ **Resolved**: Send *before* `user.delete()` so we still have `user.email` available. If the email fails to send, we still proceed with deletion (non-blocking).
2. ~~**Should the low-credits warning be one-shot (fire once when threshold crossed) or repeat every N days?**~~ **Resolved**: One-shot per threshold crossing. Tracked via `last_low_credits_warning_at` on the User model. Reset to `None` when user purchases credits.