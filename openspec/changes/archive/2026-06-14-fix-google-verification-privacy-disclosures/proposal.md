## Why

FastJob's Google API verification was rejected because the Privacy Policy page did not clearly state with whom Google user data is shared, transferred, or disclosed. While the Spanish version of the policy contains these disclosures, the English routes (`/privacy/` and `/terms/`) currently serve the Spanish template files. As a result, English-speaking Google reviewers and automated verification parsers are unable to locate the required data sharing disclosures, blocking the verification of the app.

## What Changes

- Add a fully translated English Privacy Policy template containing explicit disclosures about Google/Microsoft user data handling, sharing, and limited use.
- Add a fully translated English Terms of Service template containing general notice, service terms, and cookie disclosures.
- Modify the backend views (`PrivacyView` and `TermsView` in `apps/core/views.py`) to dynamically serve English templates when requested via the English routes (`/privacy/` and `/terms/`).
- Update the test suite (`apps/core/tests/test_views.py`) to verify Spanish assertions on Spanish routes and English assertions on English routes.

## Capabilities

### New Capabilities
<!-- Capabilities being introduced. Replace <name> with kebab-case identifier (e.g., user-auth, data-export, api-rate-limiting). Each creates specs/<name>/spec.md -->

### Modified Capabilities
<!-- Existing capabilities whose REQUIREMENTS are changing (not just implementation).
     Only list here if spec-level behavior changes. Each needs a delta spec file.
     Use existing spec names from openspec/specs/. Leave empty if no requirement changes. -->
- `legal`: The requirement is updated so that `/privacy/` and `/terms/` serve the English-translated versions of the documents rather than reusing the Spanish templates.

## Impact

- **Views**: `apps/core/views.py` (`PrivacyView`, `TermsView`)
- **Templates**: `templates/legal/` (adds `privacy_en.html` and `terms_en.html`)
- **Tests**: `apps/core/tests/test_views.py`
