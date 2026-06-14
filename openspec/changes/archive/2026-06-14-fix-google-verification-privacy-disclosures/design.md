## Context

The application has English routes defined in `config/urls.py` for `/privacy/` and `/terms/`, but they both currently map to `PrivacyView` and `TermsView` which unconditionally render the Spanish templates `templates/legal/privacy.html` and `templates/legal/terms.html`. Google verification requires that the privacy policy at the submitted English link explicitly details with whom Google user data is shared, transferred, or disclosed in English.

## Goals / Non-Goals

**Goals:**
- Provide a fully translated English Privacy Policy at `/privacy/` containing a clear, prominent disclosure of Google and Microsoft API user data sharing and transfer policies.
- Provide a fully translated English Terms of Service at `/terms/`.
- Keep existing Spanish pages fully functional and unchanged at `/privacidad/` and `/terminos/`.
- Update the test suite to verify English content on English pages and Spanish content on Spanish pages.

**Non-Goals:**
- We do not change URL paths or names in `config/urls.py`.
- We do not configure a full `.po`/`.mo` translation system for legal files, as separate template files are cleaner, easier to maintain for legal documents, and avoid additional project dependencies/compilation steps.

## Decisions

### 1. Template Splitting
- We will create two new template files in the `templates/legal/` directory:
  - `privacy_en.html`
  - `terms_en.html`
- These files will match the structure and layout of their Spanish equivalents (`privacy.html` and `terms.html`) but all text, titles, tables, and warnings will be translated to English.
- The `privacy_en.html` template will feature a visually highlighted callout containing the explicit English Google and Microsoft data sharing disclosure:
  > **Google and Microsoft Data Sharing and Disclosure:**
  > * **No sharing or transfer:** FastJob does not share, sell, rent, trade, transfer, or disclose your Google or Microsoft user data (including OAuth authentication tokens, email address, or profile information) to any third parties or external applications under any circumstances.
  > * **Exclusive use:** This data is stored securely and is used solely and exclusively to automate sending your emails (resumes/CVs) from your own account to the destination addresses you select. No data is transferred to advertising networks, data brokers, or advertising intermediaries.
  > * **Limited Use compliance:** FastJob's use and transfer to any other app of information received from Google APIs will adhere to Google API Services User Data Policy, including the Limited Use requirements.

### 2. Dynamic Template Name Selection in Views
- We will override the `get_template_names()` method in `PrivacyView` and `TermsView` inside `apps/core/views.py`.
- The method will check `self.request.resolver_match.url_name` to determine which template to serve:
  - If the name is `privacy_en`, return `['legal/privacy_en.html']`.
  - If the name is `terms_en`, return `['legal/terms_en.html']`.
  - Otherwise, fallback to the default Spanish templates.

### 3. Separation of Assertions in Tests
- Currently, `apps/core/tests/test_views.py` asserts that the English routes contain Spanish strings.
- We will update the test suite to assert English compliance strings for `test_privacy_page_english` and `test_terms_page_english`, and preserve Spanish compliance string assertions for `test_privacy_page_spanish` and `test_terms_page_spanish`.

## Risks / Trade-offs

- **Risk**: Content divergence. If the legal policies are updated in the future, developers might forget to update one of the languages.
- **Mitigation**: Add clear HTML comments at the top of each file warning developers to update both the Spanish and English templates when making changes.
