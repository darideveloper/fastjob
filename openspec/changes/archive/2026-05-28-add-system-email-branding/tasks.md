## 1. Email Layout Infrastructure

- [x] 1.1 Create `templates/email/base.html` — shared branded HTML email layout with logo (`SystemSettings.email_logo_url`), header, content block (`{% block email_content %}`), and footer (`SystemSettings.email_footer_text`). Use inline CSS, table-based header/footer, brand color (`SystemSettings.email_brand_color`). Must render in Gmail, Outlook, Apple Mail, and Graph.
- [x] 1.2 Create `apps/mailing/email.py` with `render_branded_email(subject, body_html, context=None)` helper that renders `email/base.html` with branding settings from `SystemSettings.get()`. This is a plain Python utility, not a template tag, so any app can import it directly.
- [x] 1.3 Create `templates/email/base.txt` — plain-text fallback layout with minimal structure (separator lines, footer text).
- [x] 1.4 Add `SystemSettings` fields: `email_logo_url` (URLField, default GitHub raw URL), `email_brand_color` (CharField(7), default `#007BFF`), `email_footer_text` (TextField, default `"© 2026 FastJob. Todos los derechos reservados."`), `low_credits_threshold` (IntegerField, default `0`). Include Spanish verbose names and `MinValueValidator(0)` for threshold, regex validator for hex color.
- [x] 1.5 Run `python manage.py makemigrations mailing` and verify the migration adds four columns with defaults, no data loss.
- [x] 1.6 Add the four new fields to `SystemSettingsAdmin` fieldsets with Spanish descriptions (no raw Python identifiers).
- [x] 1.7 Write tests: `test_email_branding_defaults`, `test_email_branding_custom_values`, `test_invalid_brand_color_rejected`, `test_negative_threshold_rejected`, `test_render_branded_email_wraps_content`.

## 2. Upgrade Campaign-Paused Notifications to Branded HTML

- [x] 2.1 Create `templates/email/campaign_paused_notification.html` — branded HTML for each pause reason (quota, expired, unlinked, missing_cv) with reason-specific content. Uses `email/base.html` layout.
- [x] 2.2 Create `templates/email/campaign_paused_notification.txt` — plain-text version with same content.
- [x] 2.3 Refactor `send_campaign_paused_notification` in `apps/mailing/tasks.py` to use `EmailMultiAlternatives` with both text and HTML alternatives, rendered via `render_branded_email` and Django template engine.
- [x] 2.4 Write tests: `test_paused_notification_has_html_alternative`, `test_paused_notification_reasons_covered` (quota, expired, unlinked, missing_cv), `test_paused_notification_uses_branded_layout`.

## 3. Wrap CV Outbound Emails in Branded Layout

- [x] 3.1 Update `send_cv_email` in `apps/mailing/engine.py` to call `render_branded_email(subject, body_html)` after `template.render()` and pass the wrapped HTML to `_send_via_gmail` and `_send_via_microsoft`.
- [x] 3.2 Update `_send_via_gmail` — the `body_html` parameter is now the fully wrapped HTML. No other changes needed.
- [x] 3.3 Update `_send_via_microsoft` — the `body_html` parameter is now the fully wrapped HTML. No other changes needed.
- [x] 3.4 Write tests: `test_cv_email_uses_branded_layout`, `test_cv_email_contains_logo`, `test_cv_email_contains_footer`, `test_branded_layout_preserves_template_content`.

## 4. Welcome Email

- [x] 4.1 Create `templates/email/welcome.html` — branded welcome email with greeting, credit count, onboarding steps, and links to `/dashboard/` and `/accounts/3rdparty/`.
- [x] 4.2 Create `templates/email/welcome.txt` — plain-text version.
- [x] 4.3 Create `send_welcome_email(user_pk)` Celery task in `apps/accounts/tasks.py`. Render both HTML (via branded layout) and plain-text alternatives, send with `EmailMultiAlternatives`. Log failures at WARNING level, never raise.
- [x] 4.4 Update `grant_signup_bonus` signal handler in `apps/accounts/signals.py` to call `send_welcome_email.delay(user.pk)` after granting credits. This modifies the existing signal to also dispatch the welcome email.
- [x] 4.5 Write tests: `test_welcome_email_sent_on_signup`, `test_welcome_email_mentions_credits`, `test_welcome_email_failures_logged`, `test_welcome_email_uses_first_name_or_email`.

## 5. Payment Receipt Email

- [x] 5.1 Create `templates/email/payment_receipt.html` — branded receipt with package name, price, credits granted, total balance, billing portal link, dashboard link.
- [x] 5.2 Create `templates/email/payment_receipt.txt` — plain-text version.
- [x] 5.3 Create `send_payment_receipt_email(user_pk, payment_pk)` Celery task in `apps/payments/tasks.py`. Handle `User.DoesNotExist` and `StripePayment.DoesNotExist` silently (log WARNING, return). Render and send as `EmailMultiAlternatives`.
- [x] 5.4 Update `_handle_successful_payment` in `apps/payments/views.py` to enqueue `send_payment_receipt_email.delay(user.pk, payment.pk)` after the atomic credit increment.
- [x] 5.5 Write tests: `test_receipt_email_sent_on_payment`, `test_receipt_email_shows_package_and_price`, `test_receipt_email_missing_user_logs_warning`, `test_receipt_email_uses_branded_layout`.

## 6. Low-Credits Warning Email

- [x] 6.1 Create `templates/email/low_credits_warning.html` — branded warning with current balance, link to `/payments/paquetes/`.
- [x] 6.2 Create `templates/email/low_credits_warning.txt` — plain-text version.
- [x] 6.3 Create `send_low_credits_warning(user_pk)` Celery task in `apps/mailing/tasks.py`. Render and send as `EmailMultiAlternatives`. The task itself only sends the email; the `last_low_credits_warning_at` timestamp is set atomically by the caller (see task 6.5). Log failures at WARNING level, never raise.
- [x] 6.4 Add `last_low_credits_warning_at` (DateTimeField, null=True, blank=True) to `User` model in `apps/accounts/models.py`. Include Spanish verbose name. Run `makemigrations`.
- [x] 6.5 Update `process_mailing_queue` in `apps/mailing/tasks.py` — after decrementing `credits_remaining`, check if `user.credits_remaining <= SystemSettings.get().low_credits_threshold`. If so, atomically set `last_low_credits_warning_at` using `User.objects.filter(pk=user.pk, last_low_credits_warning_at__isnull=True).update(last_low_credits_warning_at=timezone.now())`. Only enqueue `send_low_credits_warning.delay(user.pk)` if the update affected exactly one row (i.e., this is the first threshold crossing since last reset).
- [x] 6.6 Update `_handle_successful_payment` in `apps/payments/views.py` to reset `last_low_credits_warning_at = None` in the atomic update kwargs.
- [x] 6.7 Write tests: `test_low_credits_warning_fires_at_threshold`, `test_low_credits_warning_is_one_shot`, `test_low_credits_warning_resets_after_purchase`, `test_custom_threshold_fires_earlier`, `test_no_warning_above_threshold`, `test_concurrent_ticks_no_duplicate_warning`.

## 7. Account Deletion Confirmation Email

- [x] 7.1 Create `templates/email/account_deleted.html` — branded confirmation email with deletion notice, data removal note, Stripe retention note, and homepage link.
- [x] 7.2 Create `templates/email/account_deleted.txt` — plain-text version.
- [x] 7.3 Update `delete_account` in `apps/dashboard/views.py` to send an `EmailMultiAlternatives` email synchronously (not Celery) **before** `user.delete()`. Log failures at WARNING level, proceed with deletion regardless.
- [x] 7.4 Write tests: `test_deletion_email_sent_before_user_removed`, `test_deletion_email_uses_branded_layout`, `test_deletion_continues_on_email_failure`.

## 8. OAuth Link Confirmation Email

- [x] 8.1 Create `templates/email/oauth_linked.html` — branded confirmation email with provider name and dashboard link.
- [x] 8.2 Create `templates/email/oauth_linked.txt` — plain-text version.
- [x] 8.3 Create `send_oauth_link_email(user_pk, provider_name)` Celery task in `apps/accounts/tasks.py`. Render and send as `EmailMultiAlternatives`. Log failures at WARNING level.
- [x] 8.4 Add a receiver for the `social_account_added` signal from `allauth.socialaccount.signals` in `apps/accounts/signals.py` to enqueue `send_oauth_link_email.delay(user.pk, socialaccount.provider)`. This signal fires only when a new `SocialAccount` is created, not on updates.
- [x] 8.5 Write tests: `test_oauth_link_email_sent_on_google_link`, `test_oauth_link_email_sent_on_microsoft_link`, `test_oauth_link_email_not_sent_on_unlink`, `test_oauth_link_email_uses_branded_layout`.

## 9. New App Files and Migrations

- [x] 9.1 Create new file `apps/accounts/tasks.py` with `send_welcome_email` and `send_oauth_link_email` Celery tasks.
- [x] 9.2 Create new file `apps/payments/tasks.py` with `send_payment_receipt_email` Celery task.
- [x] 9.3 Run `python manage.py makemigrations accounts` to create the migration for `User.last_low_credits_warning_at`.
- [x] 9.4 Verify existing `EmailTemplate` records do not reference `{cv_url}` (handled by migration 0008, but confirm no regression).
- [x] 9.5 Run full test suite and verify no regressions in existing email send paths.

## 10. Integration and Smoke Tests

- [x] 10.1 Write an integration test: `test_all_emails_use_branded_layout` that renders every email template (welcome, receipt, low-credits, paused notification, deletion confirmation, oauth linked) and asserts each contains the logo `<img>` tag and the footer text.
- [x] 10.2 Write test: `test_branded_email_with_custom_settings` — override `SystemSettings` fields and verify the rendered email uses the custom logo URL, color, and footer text.