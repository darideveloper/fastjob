## 1. Implementation
- [x] 1.1 Update `apps/mailing/models.py` to remove `{cv_url}` from `EmailTemplate`'s `help_text` and validation.
- [x] 1.2 Create a data migration in `apps/mailing/migrations/` to update existing `EmailTemplate` records, removing the `{cv_url}` HTML links and replacing them with text stating the CV is attached.
- [x] 1.3 Update `apps/mailing/engine.py` `send_cv_email` to safely read the CV file content and pass it as an attachment payload. If `OSError` or `FileNotFoundError` occurs, pause the campaign (`user.is_campaign_active = False; user.save()`) and raise an Exception to fail the log.
- [x] 1.4 Update `apps/mailing/engine.py` `_send_via_gmail` to build a `MIMEMultipart("mixed")` containing the PDF attachment.
- [x] 1.5 Update `apps/mailing/engine.py` `_send_via_microsoft` to include the PDF in the `attachments` array of the JSON payload.
- [x] 1.6 Update `apps/mailing/tests/test_engine.py` fixtures to provide a valid, readable file for `active_cv` to prevent OSErrors.
- [x] 1.7 Update `apps/mailing/tests/test_engine.py` assertions to verify the presence and correctness of the attachment in both Gmail and Microsoft mocked payloads.