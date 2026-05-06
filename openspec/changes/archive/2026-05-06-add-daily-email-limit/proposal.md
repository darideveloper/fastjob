# Change: Add daily email limit per user

## Why
The mailing engine has no hard cap on emails per user per day, only a global slow-drip interval. To prevent abuse and protect OAuth account reputation, administrators need a configurable daily send limit per user.

## What Changes
- Add `max_emails_per_day_per_user` integer field to `SystemSettings` singleton model
- Update `process_mailing_queue` Celery task to check the 24-hour sent count per user
- Skip users who have met or exceeded the daily limit for the current queue tick

## Impact
- Affected specs: mailing
- Affected code: `apps/mailing/models.py`, `apps/mailing/tasks.py`, `apps/mailing/admin.py`, `apps/mailing/tests/test_tasks.py`, `docs/architecture.md`
