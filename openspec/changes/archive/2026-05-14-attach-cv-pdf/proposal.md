# Change: Attach CV PDF to Emails

## Why
Currently, the system sends the CV as a link, which users have identified as less effective than sending the actual PDF attachment. By attaching the PDF directly, we reduce friction for the recipient.

## What Changes
- The mailing engine (`send_cv_email`) will read the user's active CV file from storage.
- The Gmail sender (`_send_via_gmail`) will transition from a simple `MIMEMultipart("alternative")` to `MIMEMultipart("mixed")` and append the PDF as a base64 encoded attachment.
- The Microsoft sender (`_send_via_microsoft`) will append the PDF to the `"attachments"` array in the Graph API payload.
- The `{cv_url}` placeholder will be removed from `EmailTemplate`'s `help_text`.
- **BREAKING**: A data migration will update existing templates in the database to remove the HTML referencing `{cv_url}`, replacing it with a generic message indicating the CV is attached.
- If the CV file is missing from storage (e.g., deleted), the engine will catch `OSError`/`FileNotFoundError`, pause the user's campaign (`is_campaign_active = False`), and mark the attempt as failed.

## Impact
- Affected specs: `mailing`
- Affected code: `apps/mailing/engine.py`, `apps/mailing/models.py`, `apps/mailing/tests/test_engine.py`.