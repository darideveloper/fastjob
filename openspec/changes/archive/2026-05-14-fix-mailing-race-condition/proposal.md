# Change: Fix Mailing Queue Race Condition

## Why
When the `process_mailing_queue` Celery task takes longer than 1 minute to finish (due to high volume or slow APIs), Celery spawns a second, concurrent instance of the task. Because there is no concurrency control, both tasks process the same users simultaneously, violating the 5-minute wait time, daily limits, and company cooldowns.

## What Changes
- Add a Single Task Lock using Django's cache in `apps/mailing/tasks.py`.
- Ensure the `process_mailing_queue` task attempts to acquire this atomic lock before proceeding.
- If the lock is already held, the task logs a message and exits early.
- The lock is always released when the task finishes.

## Impact
- Affected specs: mailing
- Affected code: `apps/mailing/tasks.py`, `apps/mailing/tests/test_tasks.py`