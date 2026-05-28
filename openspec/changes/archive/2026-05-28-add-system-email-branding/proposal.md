# Change: Add branded system emails and notification infrastructure

## Why

FastJob currently sends only two categories of email, and both are bare-bones:

1. **CV outbound emails** — rendered from `EmailTemplate.body_html` stored in the DB as raw inline-styled HTML with no shared layout, logo, branding, or visual identity.
2. **Campaign-paused notifications** — plain text sent via Django's `send_mail()`, no HTML, no logo, no styling.

Missing system/notification emails that every SaaS product should send:

- **Welcome/onboarding email** — users get signup credits via the `user_signed_up` signal but receive no email telling them how to get started.
- **Payment confirmation/receipt** — `_handle_successful_payment()` grants credits but never emails the buyer. No Stripe receipt link, no confirmation.
- **Low-credits exhaustion warning** — `can_send()` silently returns `False` and the campaign stops. No email nudges the user to buy more.
- **Account deletion confirmation** — `delete_account()` wipes the user without sending a goodbye email (GDPR best practice).
- **OAuth link confirmation** — no "your Google/Microsoft account was connected" confirmation for security awareness.

Additionally, the CV outbound templates need a shared branded email layout (logo, header, footer, unsubscribe link) so that every email FastJob sends — whether system or campaign — looks like it comes from the same product.

## What Changes

- **ADDED**: Shared email layout system — a reusable HTML email template (`templates/email/base.html`) with logo, brand colors, and footer that wraps all outgoing emails.
- **ADDED**: Welcome email — sent via a Celery task triggered by `user_signed_up` signal, with onboarding steps (upload CV, link OAuth, start campaign).
- **ADDED**: Payment receipt email — sent from `_handle_successful_payment()` via Celery task, confirming amount paid, credits granted, and providing a Stripe billing portal link.
- **ADDED**: Low-credits warning email — sent from `process_mailing_queue` when a user's credits drop to 0 or below a configurable threshold.
- **ADDED**: Account deletion confirmation email — sent from `delete_account()` before the user record is destroyed.
- **MODIFIED**: Campaign-paused notifications — upgrade from plain text `send_mail()` to `EmailMultiAlternatives` using the branded layout.
- **MODIFIED**: CV outbound `EmailTemplate.render()` — inject the rendered template body into the shared branded email wrapper.
- **ADDED**: `SystemSettings` email branding fields for configurable logo URL, brand colors, footer text, and low-credits threshold.

## Impact

- Affected specs: `mailing`, `accounts`, `pricing` (new spec deltas for each)
- Affected code: `apps/mailing/tasks.py`, `apps/mailing/engine.py`, `apps/mailing/models.py`, `apps/accounts/signals.py`, `apps/accounts/models.py`, `apps/payments/views.py`, new files `apps/accounts/tasks.py` and `apps/payments/tasks.py`, new template files under `templates/email/`, new utility `apps/mailing/email.py`.
- **BREAKING**: None — existing email content is preserved; we add a layout wrapper around it.
- Migrations: One for `SystemSettings` (4 new fields), one for `User` (1 new field). Both additive, no data loss.