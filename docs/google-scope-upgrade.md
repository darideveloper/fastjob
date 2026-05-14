# Google OAuth Scope Upgrade: gmail.modify

This project has upgraded its Gmail OAuth scope from `gmail.send` to `gmail.modify`. This change allows the system to delete sent messages from the user's "Sent" folder based on global visibility settings.

## Required Actions

### 1. Google Cloud Console Configuration
- Go to the [Google Cloud Console](https://console.cloud.google.com/).
- Navigate to **APIs & Services > OAuth consent screen**.
- Edit your app registration.
- In the **Scopes** section, add `https://www.googleapis.com/auth/gmail.modify`.
- Remove `https://www.googleapis.com/auth/gmail.send`.

### 2. CASA Security Audit
The `gmail.modify` scope is a **Restricted** scope. Using it requires your application to undergo a Cloud App Security Assessment (CASA) Tier 2 or Tier 3 audit.
- This process involves a security assessment by a Google-authorized third-party lab.
- There are significant costs and time commitments associated with this audit.
- For more information, see the [OAuth Application Verification FAQ](https://support.google.com/cloud/answer/10311615).

### 3. User Re-authentication
Existing users who have linked their Google accounts will need to re-authenticate and consent to the new `gmail.modify` permission. The system will prompt them to re-link their account the next time they attempt to use mailing features if their token is invalid or if you force a re-login.
