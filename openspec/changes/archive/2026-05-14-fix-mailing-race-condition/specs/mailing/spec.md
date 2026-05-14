## ADDED Requirements
### Requirement: Mailing Queue Concurrency Safety

The system MUST ensure that only one instance of the `process_mailing_queue` background task executes at any given time to prevent race conditions that bypass sending intervals and daily limits. This MUST be implemented using an atomic distributed lock via the application cache. If the lock cannot be acquired, the task MUST exit early without processing any emails. The lock MUST be released when the task finishes execution, and MUST have a timeout fallback to prevent deadlocks in case of worker failure.

#### Scenario: Concurrent task execution is blocked
- **GIVEN** an instance of `process_mailing_queue` is currently running and holding the lock
- **WHEN** a second instance of `process_mailing_queue` is triggered by Celery Beat
- **THEN** the second instance fails to acquire the lock
- **AND** it logs that it is skipping the tick
- **AND** it exits immediately without sending any emails or updating database state

#### Scenario: Lock is released after successful execution
- **GIVEN** an instance of `process_mailing_queue` successfully acquires the lock
- **WHEN** the task completes processing the queue
- **THEN** the lock is deleted from the cache
- **AND** subsequent task triggers are able to acquire the lock

#### Scenario: Lock is released after an exception
- **GIVEN** an instance of `process_mailing_queue` successfully acquires the lock
- **WHEN** an unhandled exception occurs during processing
- **THEN** the task ensures the lock is still deleted from the cache via a `finally` block before bubbling up the exception