## Why

The application needs to align its public legal pages with the updated terms provided by the legal consultant (under the entity FERNANDO PEÑA TORRE). Additionally, the Google Developer verification team has requested explicit disclosures regarding how Google user data is shared, transferred, or disclosed, and expects the pages to be accessible at the standard `/privacy` and `/terms` paths.

## What Changes

- Add URL routing patterns for `/privacy/` and `/terms/` in `config/urls.py` to satisfy Google's specific verification link requirements, while retaining the existing `/privacidad/` and `/terminos/` paths for backwards-compatibility.
- Restructure the Privacy Policy (`/privacidad/` and `/privacy/`) to replace the current text with the consultant's structured tables for Service Contracting and Contacts, while preserving crucial product-specific technical declarations (DigitalOcean storage, 5-minute UUIDs, global blacklist, Stripe payments).
- Add the explicit Google user data sharing and transfer disclosures requested by the Google verification team on the Privacy Policy page.
- Restructure the Terms of Service / Legal Notice (`/terminos/` and `/terms/`) to incorporate general company identification details (CIF, Registry, Address), unsecured communication warnings, a comprehensive Cookie Policy with browser removal links, and a Social Media Privacy Policy for Instagram.
- Preserve the existing Terms disclaimers concerning the "Envíos" credit system, lack of recruiting agency status, and email account suspension liability.

## Capabilities

### New Capabilities

*(None)*

### Modified Capabilities

- `legal`: The requirements for both the Privacy Policy page and the Terms of Service page are changing to support both English (`/privacy/`, `/terms/`) and Spanish (`/privacidad/`, `/terminos/`) URL paths, while incorporating the new consultant content, Google compliance sharing disclosures, and detailed Cookie/Social media policies.

## Impact

- Affected templates: `templates/legal/privacy.html` and `templates/legal/terms.html`.
- Affected URL configuration: `config/urls.py` (to add support for `/privacy/` and `/terms/`).
- No backend database migrations are required.
