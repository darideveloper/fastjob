# ResumeLink — Documentation

**ResumeLink** is a Django SaaS (server-side rendered) that helps job-seekers automatically send their CV to a curated database of companies, using **their own Gmail or Outlook account via OAuth2**. The platform is engineered for maximum email deliverability: no PDF attachments, randomized email content, slow-drip sending, and per-company cooldown windows.

---

## Why ResumeLink exists

Mass-mailing a CV using generic tools (SendGrid, Mailchimp, even a Gmail alias) lands in the spam folder or gets the sender blacklisted within hours. ResumeLink solves this by:

- **Sending from the user's real inbox** — preserves sender reputation, passes SPF/DKIM naturally.
- **Never attaching a PDF** — attachments trigger spam filters; we send a unique UUID-obfuscated download link instead.
- **Slow-drip cadence** — one email per user every 5 minutes, with a 12-hour cooldown per recipient company.
- **Random subject + body per send** — prevents "footprint" detection by anti-spam systems.
- **Unsubscribe in every email** — one click → permanent blacklist; no recipient ever receives a second email after opting out.

---

## Tech stack at a glance

| Layer | Choice |
|---|---|
| Framework | Django 4.2 (monolith, SSR) |
| Database | PostgreSQL |
| Queue / Scheduling | Celery + Redis + django-celery-beat |
| Authentication | django-allauth (Google + Microsoft OAuth2) |
| File storage | DigitalOcean Spaces (S3-compatible) |
| Payments | Stripe (EUR) |
| Frontend | Django templates + Tailwind CDN |
| Observability | structured logging + Sentry |

---

## How to read these docs

1. **First time setting up the project?** → [`run.md`](run.md)
2. **Deploying to a server?** → [`deploy.md`](deploy.md)
3. **Want a system-wide picture?** → [`architecture.md`](architecture.md)
4. **Diving into a specific feature?** → use the table below.

---

## Feature documentation

Each feature doc covers: **tech specs**, **user perspective**, **admin perspective**, configuration, and (where useful) diagrams + examples.

| Feature | Doc | Summary |
|---|---|---|
| Authentication | [`features/authentication.md`](features/authentication.md) | OAuth2 login with Google (`gmail.send`) and Microsoft (`Mail.Send`). No passwords. |
| CV management | [`features/cv-management.md`](features/cv-management.md) | PDF upload, private S3 storage, short-lived pre-signed download URLs, per-send UUID obfuscation. |
| Mailing engine | [`features/mailing-engine.md`](features/mailing-engine.md) | The core: slow-drip, randomization, OAuth token refresh, Gmail / Graph API integration. |
| Email templates | [`features/email-templates.md`](features/email-templates.md) | Admin-managed randomized subject + body pairs with placeholder substitution. |
| Companies database | [`features/companies.md`](features/companies.md) | Excel (`.xlsx`) importer, area/location metadata, per-user filters. |
| Blacklist & Unsubscribe | [`features/blacklist-unsubscribe.md`](features/blacklist-unsubscribe.md) | One-click opt-out, global blacklist, idempotent. |
| Credits system | [`features/credits.md`](features/credits.md) | 1 email = 1 credit; 5-credit signup bonus; never expires. |
| Payments | [`features/payments.md`](features/payments.md) | Stripe Checkout, EUR, packages configurable via admin; webhooks idempotent. |
| User dashboard | [`features/user-dashboard.md`](features/user-dashboard.md) | CV upload, filters, campaign toggle, credit balance, activity log. |
| Admin panel | [`features/admin-panel.md`](features/admin-panel.md) | Companies, templates, blacklist, packages, mailing logs, system settings. |
| Re-link notifications | [`features/notifications.md`](features/notifications.md) | Email to user when OAuth token expires; auto-pauses campaign. |
| Security | [`features/security.md`](features/security.md) | Rate limiting, security headers, CSRF, cookie hardening. |
| Monitoring & testing | [`features/monitoring.md`](features/monitoring.md) | Structured logging, Sentry, pytest suite. |

---

## Conventions used in these docs

- **Files and line-level code references** look like `apps/mailing/engine.py:142` so you can jump straight to the source.
- **Mermaid diagrams** are used for flows and state machines. They render natively in GitHub, GitLab, Bitbucket, and most modern markdown editors.
- **Env vars** are always documented inline where relevant, and aggregated in [`run.md`](run.md) + [`deploy.md`](deploy.md).
- **Admin perspective** and **user perspective** sections describe the UX from each actor's point of view — useful both for onboarding and for writing marketing copy.

---

## Also see

- [`../log.md`](../log.md) — development log with what's done, what's pending, by priority.
- [`../README.md`](../README.md) — terse README for the repo root.
