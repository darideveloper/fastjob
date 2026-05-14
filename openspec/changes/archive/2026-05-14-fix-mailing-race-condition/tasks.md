## 1. Implementation
- [x] 1.1 Update `apps/mailing/tasks.py` to import Django's `cache`.
- [x] 1.2 Modify `process_mailing_queue` to attempt acquiring a cache lock using `cache.add` with a timeout of 10 minutes (600 seconds).
- [x] 1.3 Add early exit logic if `cache.add` returns `False`, including a log message indicating the task was skipped due to an existing lock.
- [x] 1.4 Wrap the main logic of `process_mailing_queue` inside a `try...finally` block.
- [x] 1.5 Implement lock release inside the `finally` block using `cache.delete`.
- [x] 1.6 Update `apps/mailing/tests/test_tasks.py` to add a unit test verifying that when the cache lock is already acquired, `process_mailing_queue` exits early without processing.
- [x] 1.7 Add a unit test verifying that the cache lock is released correctly after execution, even if an exception occurs.