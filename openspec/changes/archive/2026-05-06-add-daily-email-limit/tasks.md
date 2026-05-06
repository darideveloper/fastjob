# Tasks for add-daily-email-limit

## 1. Model
- [x] 1.1 Add `max_emails_per_day_per_user = models.IntegerField(default=50, help_text="Límite máximo de correos por usuario en 24 horas")` to `SystemSettings` in `apps/mailing/models.py`
- [x] 1.2 Run `python manage.py makemigrations mailing` to generate the migration

## 2. Admin
- [x] 2.1 Add `max_emails_per_day_per_user` to the existing `"Motor de Envío (Slow-Drip)"` fieldset in `SystemSettingsAdmin` (`apps/mailing/admin.py`) — the admin uses explicit `fieldsets` so the field will not appear automatically

## 3. Queue enforcement
- [x] 3.1 After reading `cfg = SystemSettings.get()` (already at the top of `process_mailing_queue`), also read `cfg.max_emails_per_day_per_user`
- [x] 3.2 Before processing each user, annotate the `active_users` queryset with `sent_last_24h` — a `Count` of `MailingLog` rows with `status=SENT` and `sent_at__gte=now - timedelta(hours=24)` for that user — to avoid an N+1 query per user
- [x] 3.3 At the start of the per-user loop, skip (`continue`) any user whose `sent_last_24h >= max_emails_per_day_per_user`

## 4. Tests
- [x] 4.1 Update the `settings_obj` fixture in `apps/mailing/tests/test_tasks.py` to include `max_emails_per_day_per_user` in its `defaults` dict (use a value high enough — e.g., `1000` — so existing tests are unaffected)
- [x] 4.2 Add test: user whose `sent_last_24h == max_emails_per_day_per_user` is skipped by `process_mailing_queue`
- [x] 4.3 Add test: user whose `sent_last_24h == max_emails_per_day_per_user - 1` receives an email
- [x] 4.4 Add test: `max_emails_per_day_per_user=0` causes all users to be skipped

## 5. Documentation
- [x] 5.1 Update the `SystemSettings` entry in `docs/architecture.md` (line 77) to mention the new `max_emails_per_day_per_user` field
