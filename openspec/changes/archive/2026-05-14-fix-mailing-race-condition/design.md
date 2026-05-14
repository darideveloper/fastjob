## Context
The `process_mailing_queue` background task in Celery runs every minute to process outgoing emails. If the queue processing takes longer than one minute, Celery Beat spawns a concurrent task. This causes race conditions where both tasks read the same database state and attempt to send emails simultaneously, violating the business logic limits (5-minute intervals, daily limits, company cooldowns).

## Goals / Non-Goals
- **Goals**: Prevent multiple instances of `process_mailing_queue` from running at the same time using a distributed lock. Ensure the lock is safely released on task completion or failure.
- **Non-Goals**: Introduce complex third-party locking libraries (e.g., Redlock) or refactor the entire mailing queue into per-user sub-tasks.

## Decisions
- **Decision**: Use Django's built-in `cache.add()` as a simple distributed atomic lock.
- **Why**: The project already uses Redis for its cache backend, so `cache.add()` is atomic and fast. This is the simplest approach that effectively solves the race condition without adding new infrastructure or dependencies.
- **Alternatives considered**: 
  - **Splitting into sub-tasks (e.g., `process_user(user.pk)`)**: While more scalable because it avoids blocking the whole queue if one user is slow, it requires significantly more refactoring and introduces complexity in handling per-user locks. We prioritize simplicity first.

## Risks / Trade-offs
- **Risk**: A worker crashes catastrophically (e.g., OOM kill) before hitting the `finally` block, leaving the lock active indefinitely.
- **Mitigation**: Use a timeout of 10 minutes when acquiring the lock (`cache.add("key", "value", timeout=600)`). If the worker crashes, the cache key will naturally expire after 10 minutes, allowing the queue to resume. The trade-off is a potential 10-minute downtime for the mailing engine in rare crash scenarios, which is acceptable for a slow-drip campaign system.