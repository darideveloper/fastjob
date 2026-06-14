## 1. Modify Template Files

- [x] 1.1 Remove OAuth link instructions from `templates/email/welcome.txt`
- [x] 1.2 Remove OAuth link instructions from `templates/email/welcome.html`
- [x] 1.3 Update campaign paused notification wording for expired tokens in `templates/email/campaign_paused_notification.txt`
- [x] 1.4 Update campaign paused notification wording for expired tokens in `templates/email/campaign_paused_notification.html`

## 2. Disable Redundant OAuth Signal

- [x] 2.1 Remove the `@receiver(social_account_added)` decorator from `notify_oauth_link` in `apps/accounts/signals.py` to prevent redundant emails during signup

## 3. Verify and Test

- [x] 3.1 Run django-allauth tests to verify that no regressions are introduced
- [x] 3.2 Run accounts and mailing tests to ensure all tests pass successfully
