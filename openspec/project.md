# Project Context

## Purpose
FastJob is a Django-based SaaS designed to automate the process of sending CVs to company databases. It enables job seekers to send personalized applications directly from their own Gmail or Outlook accounts via OAuth2. The system is architected for maximum deliverability by using a "slow-drip" mailing engine, randomized email templates, and providing CVs via time-limited links instead of attachments.

## Tech Stack
- **Backend**: Django 4.2 (Server-Side Rendering)
- **Database**: PostgreSQL
- **Task Queue & Cache**: Celery + Redis (separate Redis DBs for tasks and cache)
- **Authentication**: django-allauth with Google (Gmail API `gmail.send`) and Microsoft (Graph API `Mail.Send`) OAuth2
- **File Storage**: DigitalOcean Spaces (S3 compatible) for CV PDFs
- **Payments**: Stripe (EUR) for credit packages
- **Frontend**: Django Templates + Tailwind CSS (via CDN)
- **Monitoring**: Sentry (error tracking), Flower (Celery monitoring)

## Project Conventions

### Code Style
- **Python**: Adheres to idiomatic Python and Django practices.
- **Settings**: Configuration is managed via `python-decouple`, keeping secrets in `.env`.
- **Localization**: Language is set to Spanish (`es`), and the timezone is `Europe/Madrid`.
- **Logging**: Console-based structured logging for Docker/PaaS compatibility.
- **Templates**: Standard Django Template Language (DTL) with Tailwind classes.

### Architecture Patterns
- **Monolithic Design**: All core features (auth, mailing, payments) reside in a single codebase for operational simplicity.
- **Modular Apps**: Code is organized into functional apps under the `apps/` directory (e.g., `apps.accounts`, `apps.mailing`).
- **Slow-Drip Engine**: Celery Beat schedules mailing tasks to ensure emails are sent at controlled intervals, mimicking human behavior.
- **Link over Attachment**: CVs are shared via UUID-scrambled links to signed S3 URLs to avoid spam filters.
- **OAuth Send**: Uses the user's personal reputation by sending from their own authorized accounts rather than a central SMTP server.

### Testing Strategy
- **Framework**: `pytest` with `pytest-django`.
- **Location**: Tests are co-located within each app's `tests/` directory.
- **Fixtures**: Shared fixtures (e.g., users, linked accounts, companies) are maintained in `conftest.py`.
- **Markers**: Uses `@pytest.mark.slow` for tests interacting with external services.
- **CI**: GitHub Actions workflow (`ci.yml`) runs tests on push/PR.

### Git Workflow
- **Branching**: (Standard feature branching recommended).
- **Commit Messages**: Follows [Conventional Commits](https://www.conventionalcommits.org/) (e.g., `feat(mailing): add new email template`).

## Domain Context
- **Envíos**: Users buy envíos to send CVs. One envío equals one email sent to one company.
- **Campaigns**: A set of parameters (filters, active status) that governs the automated sending process for a user.
- **Blacklist**: A list of emails that have unsubscribed, preventing further sends to them.
- **Cool-down**: A per-company limit (default 12 hours) to avoid double-emailing the same company too quickly.

## Important Constraints
- **Deliverability**: Avoid any patterns that look like mass-spam (no attachments, varied templates, slow rate).
- **OAuth Tokens**: Long-running token correctness is governed by the OAuth requirements in `specs/mailing/spec.md` — rotated refresh tokens must be persisted (Microsoft rotates on every refresh), transient upstream errors must not pause campaigns, and `GOOGLE_OAUTH_PROJECT_MODE` / `MICROSOFT_TENANT` env vars are surfaced via `/healthz` and `manage.py check_oauth_config`.
- **Privacy**: CVs are sensitive; access via links must be time-limited and logged.

## External Dependencies
- **Google Cloud Console**: For Gmail API access.
- **Azure Portal**: For Microsoft Graph API access.
- **Stripe**: For payment processing and webhooks.
- **DigitalOcean Spaces**: For secure object storage.
- **Sentry**: For real-time error reporting.
