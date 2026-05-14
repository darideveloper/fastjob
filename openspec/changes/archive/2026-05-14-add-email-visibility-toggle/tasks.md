## 1. System Configuration
- [x] 1.1 Create `SystemConfig` singleton model in `apps/core/models.py` with a boolean field `save_emails_to_sent_folder` (default: `False`).
- [x] 1.2 Run migrations `python manage.py makemigrations core` and `python manage.py migrate`.
- [x] 1.3 Register `SystemConfig` in `apps/core/admin.py` to be editable from the Django Admin dashboard.

## 2. OAuth Scope Updates
- [x] 2.1 Update `config/settings.py` to replace `https://www.googleapis.com/auth/gmail.send` with `https://www.googleapis.com/auth/gmail.modify` in `SOCIALACCOUNT_PROVIDERS['google']['SCOPE']`.
- [x] 2.2 Add instructions in project documentation (`docs/`) outlining the Google Cloud Console updates and CASA audit required for the new restricted scope.

## 3. Mailing Engine Updates
- [x] 3.1 Update `_send_via_microsoft` in `apps/mailing/engine.py` to fetch the `SystemConfig` and set `saveToSentItems` accordingly.
- [x] 3.2 Update `_send_via_gmail` in `apps/mailing/engine.py` to capture the `id` from the send response.
- [x] 3.3 Add logic in `_send_via_gmail` to call the Gmail API delete/trash endpoint using the message `id` if the global `SystemConfig.save_emails_to_sent_folder` is `False`.

## 4. Testing
- [x] 4.1 Write tests in `apps/core/tests/` to verify the `SystemConfig` singleton behavior.
- [x] 4.2 Update existing tests in `apps/mailing/tests/test_engine.py` to mock `SystemConfig` and verify the `saveToSentItems` payload for Microsoft.
- [x] 4.3 Add tests in `apps/mailing/tests/test_engine.py` to verify the Gmail deletion call is made when the global visibility is disabled and skipped when enabled.
