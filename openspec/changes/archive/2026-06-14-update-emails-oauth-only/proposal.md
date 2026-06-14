## Why

FastJob is an OAuth-only platform where users sign up and log in exclusively using Google or Microsoft accounts. However, some system email templates contain outdated recommendations (such as telling already-signed-up users to link their Google/Microsoft accounts) or confusing messages (such as saying a campaign has "expired" when it actually means the OAuth token has expired and they need to log in again). Aligning these email templates with our authentication constraints improves user experience and avoids confusion.

## What Changes

- **Modified Welcome Email**: Remove instructions advising users to link Google/Microsoft accounts, as they are already authenticated via OAuth to sign up.
- **Modified Campaign Paused Notification Email**: Correct the message for token/session expiration (`expired` reason) from "your campaign has expired" to "your email connection has expired, please log in again to renew it".
- **Redundant OAuth Link Email**: Clean up or acknowledge the redundancy of the separate "OAuth linked" notification sent upon first signup.

## Capabilities

### New Capabilities
<!-- None needed -->

### Modified Capabilities
- `accounts`: Update welcome email instructions to reflect that the OAuth account is already linked upon registration.
- `mailing`: Update campaign paused email instructions to correctly explain token expiration and direct users to log in again.

## Impact

- Modified files:
  - `templates/email/welcome.txt`
  - `templates/email/welcome.html`
  - `templates/email/campaign_paused_notification.txt`
  - `templates/email/campaign_paused_notification.html`
- Impacted systems:
  - Accounts app (Welcome email flow)
  - Mailing app (Campaign pausing and notifications flow)
