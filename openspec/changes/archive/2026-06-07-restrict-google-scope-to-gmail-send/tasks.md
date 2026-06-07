## 1. Settings & Scope

- [x] 1.1 Change `SOCIALACCOUNT_PROVIDERS['google']['SCOPE']` from `gmail.modify` to `gmail.send` in `config/settings.py`

## 2. Model & Admin

- [x] 2.1 Remove `save_emails_to_sent_folder` field from `SystemSettings` model in `apps/mailing/models.py`
- [x] 2.2 Remove "Visibilidad de Correos" fieldset from `SystemSettingsAdmin` in `apps/mailing/admin.py`

## 3. Mailing Engine

- [x] 3.1 Remove conditional trash logic (lines 297-309) from `_send_via_gmail` in `apps/mailing/engine.py`
- [x] 3.2 Remove `SystemSettings.get().save_emails_to_sent_folder` conditional from `_send_via_microsoft` in `apps/mailing/engine.py` — always pass `"saveToSentItems": true`

## 4. Migration

- [x] 4.1 Generate a new Django migration to remove the `save_emails_to_sent_folder` column from `mailing_systemsettings`

## 5. Tests

- [x] 5.1 Remove or rewrite `test_send_cv_email_via_google_honors_visibility_disabled_by_trashing` and `test_send_cv_email_via_google_honors_visibility_enabled_by_not_trashing` in `apps/mailing/tests/test_engine.py`
- [x] 5.2 Remove all `SystemSettings.objects.update_or_create(pk=1, defaults={"save_emails_to_sent_folder": ...})` lines from test setup — 7 occurrences across `test_engine.py` (lines 113, 246, 789, 929, 940, 951, 968)
- [x] 5.3 Run test suite to confirm all tests pass

## 6. Spec Update

- [x] 6.1 Remove the `Global Email Visibility Toggle` requirement and related scenarios from `openspec/specs/mailing/spec.md`
- [x] 6.2 Update the `Email API Integration` requirement in `openspec/specs/mailing/spec.md` to remove visibility variant scenarios

## 7. Legal & README

- [x] 7.1 Update `templates/legal/privacy.html` — change `gmail.modify` to `gmail.send`
- [x] 7.2 Update `openspec/specs/legal/spec.md` — change scope reference from `gmail.modify` to `gmail.send`
- [x] 7.3 Update `README.md` — change scope reference in line 12 and setup instructions in line 46
- [x] 7.4 Document in deploy checklist that Google Cloud Console OAuth consent screen scope must be updated from `gmail.modify` to `gmail.send`
