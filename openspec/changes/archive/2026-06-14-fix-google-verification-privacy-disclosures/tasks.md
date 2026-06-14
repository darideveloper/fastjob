## 1. Templates

- [x] 1.1 Create `templates/legal/privacy_en.html` as an English translation of `templates/legal/privacy.html`. Include the prominent Google/Microsoft Data Sharing and Disclosure block.
- [x] 1.2 Create `templates/legal/terms_en.html` as an English translation of `templates/legal/terms.html`.

## 2. Views and Routing

- [x] 2.1 Modify `PrivacyView` and `TermsView` in `apps/core/views.py` to override `get_template_names()` and dynamically route requests to the English templates when accessed via the English URL names (`privacy_en` and `terms_en`).

## 3. Test Updates and Verification

- [x] 3.1 Update `test_privacy_page_english` in `apps/core/tests/test_views.py` to assert English compliance strings instead of Spanish ones.
- [x] 3.2 Update `test_terms_page_english` in `apps/core/tests/test_views.py` to assert English compliance strings instead of Spanish ones.
- [x] 3.3 Run the test suite via `pytest` to ensure all core tests pass successfully.
