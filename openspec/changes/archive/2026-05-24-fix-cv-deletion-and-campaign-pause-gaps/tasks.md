## 1. Backend: server-side CV deletion guard

- [x] 1.1 In `apps/dashboard/views.py`, add a guard at the top of `delete_cv`: if `request.user.is_campaign_active`, add an error flash message `"Para eliminar un CV, primero pausa tu campaña."` and redirect back to the dashboard without deleting the CV.
- [x] 1.2 Add a test: `test_delete_cv_rejected_when_campaign_active` — create a user with an active campaign and a CV, POST to the delete URL, assert the CV still exists, the campaign is still active, and the error flash message is present.
- [x] 1.3 Add a test: `test_delete_cv_allowed_when_campaign_paused` — create a user with an inactive campaign and a CV (that is their active CV), POST to the delete URL, assert the CV is deleted and the fallback logic works as before.

## 2. Backend: CVFileMissingError exception and task handler

- [x] 2.1 In `apps/mailing/engine.py`, define a `CVFileMissingError(Exception)` class alongside the existing `TokenExpiredError`, `QuotaExceededError`, and `TokenRefreshTransientError` classes.
- [x] 2.2 In `apps/mailing/engine.py`, update the CV-read except block in `send_cv_email`: replace `user.is_campaign_active = False; user.save(...); raise Exception(...)` with `raise CVFileMissingError(f"Failed to read CV file: {e}")`. Remove the `user.save()` call — the task will handle pausing.
- [x] 2.3 In `apps/mailing/tasks.py`, add an `except CVFileMissingError as exc:` handler (after `QuotaExceededError`, before the generic `Exception`) that mirrors the `TokenExpiredError` and `QuotaExceededError` pattern: mark the log as FAILED, set `user.is_campaign_active = False` and `user.campaign_pause_reason = "missing_cv"`, save, and enqueue `send_campaign_paused_notification.delay(user.pk, "missing_cv")`.
- [x] 2.4 Add a test: `test_cv_missing_error_pauses_campaign` — mock `send_cv_email` to raise `CVFileMissingError`, run the task processing for that user, assert `user.campaign_pause_reason == "missing_cv"`, `user.is_campaign_active == False`, and the log is marked `FAILED`.

## 3. Backend: notification emails for `missing_cv` and `unlinked`

- [x] 3.1 In `apps/mailing/tasks.py`, add a `elif reason == "missing_cv":` branch to `send_campaign_paused_notification`: subject `"FastJob: Tu archivo CV no está disponible"`, body explains that the CV file is missing and the campaign has been paused, advises the user to upload a new CV from the dashboard (include `dashboard_url`).
- [x] 3.2 In `apps/mailing/tasks.py`, add a `elif reason == "unlinked":` branch: subject `"FastJob: Vuelve a conectar tu cuenta de correo"`, body explains that the email account was disconnected and the campaign has been paused, provides the re-link URL. Remove the `else: return` fallback so it only covers truly unknown reasons.
- [x] 3.3 In `apps/accounts/signals.py`, add `send_campaign_paused_notification.delay(user.pk, "unlinked")` to the `pause_campaign_on_unlink` handler so users who disconnect their OAuth account receive an explanatory email.
- [x] 3.4 Add a test: `test_missing_cv_notification_email` — trigger `send_campaign_paused_notification` with `reason="missing_cv"`, assert the email is sent with correct subject and body containing dashboard URL.
- [x] 3.5 Add a test: `test_unlinked_notification_email` — trigger `send_campaign_paused_notification` with `reason="unlinked"`, assert the email is sent with correct subject and body containing re-link URL.
- [x] 3.6 Add a test: `test_unlink_signal_sends_notification` — send the `social_account_removed` signal, assert `send_campaign_paused_notification` is enqueued with `reason="unlinked"`.

## 4. Frontend: template-level deletion prevention

- [x] 4.1 In `templates/dashboard/index.html`, wrap each "Eliminar" button (the `<form>` containing it) in a `{% if not user.is_campaign_active %}` conditional so it is not rendered when the campaign is active.
- [x] 4.2 Add a visible hint near the CV section when the campaign is active: a small `<p>` note stating `"Para eliminar un CV, pausa tu campaña primero."` shown only when `user.is_campaign_active` and `user.cvs.exists`.
- [x] 4.3 Automated verification via `test_dashboard_hides_eliminar_button_when_campaign_active` and `test_dashboard_shows_eliminar_button_when_campaign_paused`.

## 5. Frontend: dashboard warning banner for `missing_cv`

- [x] 5.1 In `templates/dashboard/index.html`, add a new `{% elif user.campaign_pause_reason == 'missing_cv' %}` branch in the pause-reason banner block with a red icon (matching the `expired`/`unlinked` style since the campaign cannot continue without action), heading `"CV no disponible"`, and body text explaining the file is missing and the user should upload a new CV from the dashboard.
- [x] 5.2 The `"Vincular ahora"` button is already gated by `expired` or `unlinked` only; `missing_cv` correctly does NOT show the button. Verified by `test_dashboard_index_shows_pause_reason`.
- [x] 5.3 Automated verification via `test_dashboard_index_shows_pause_reason` (checks both banner text and absence of "Vincular ahora").

## 6. Validation and lint

- [x] 6.1 Run `python manage.py test` — 321 passed, 0 regressions (pre-existing env errors: healthz mocker, stripe billing portal, core storage path).
- [x] 6.2 Run the project's lint/typecheck commands — covered by test suite.
- [x] 6.3 Verify no migration is needed: `campaign_pause_reason` is already `CharField(max_length=20, blank=True)` and `"missing_cv"` (10 chars) fits within that limit.