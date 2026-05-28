# Tasks: Update Company Logo URL

- [x] **Implementation**
  - [x] Update `SystemSettings.email_logo_url` default and `verbose_name` in `apps/mailing/models.py`
  - [x] Create a new migration for `mailing` app to update the `email_logo_url` default, `verbose_name`, and existing record
- [x] **Tests Update**
  - [x] Update `apps/payments/tests/test_payment_email.py`
  - [x] Update `apps/mailing/tests/test_paused_notification_branded.py`
  - [x] Update `apps/mailing/tests/test_email_branding.py`
  - [x] Update `apps/mailing/tests/test_cv_email_branded.py`
  - [x] Update `apps/dashboard/tests/test_deletion_email.py`
  - [x] Update `apps/accounts/tests/test_oauth_email.py`
- [x] **Validation**
  - [x] Run `pytest apps/mailing/tests/test_email_branding.py`
  - [x] Run `pytest apps/mailing/tests/test_cv_email_branded.py`
  - [x] Run `pytest apps/payments/tests/test_payment_email.py`
  - [x] Run `pytest apps/dashboard/tests/test_deletion_email.py`
  - [x] Run `pytest apps/accounts/tests/test_oauth_email.py`
