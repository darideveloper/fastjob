## 1. Privacy Policy Template Restructure & Routing

- [x] 1.1 Restructure `templates/legal/privacy.html` using the new consultant's structured tables for Service Contracting and Contact Forms.
- [x] 1.2 Insert the Google User Data Sharing and Transfer disclosures callout stating that no Google data is shared with third parties.
- [x] 1.3 Merge product-specific technical clauses (DigitalOcean Spaces storage, 5-minute UUID transient download links, global blacklist opt-out, and Stripe transaction logs) into the restructured layout.
- [x] 1.4 Update the contact info for exercising GDPR rights to point to `dpo@basquekide.es`.
- [x] 1.5 Add URL routing pattern for `/privacy/` in `config/urls.py` pointing to `PrivacyView`.

## 2. Terms of Service / Legal Notice Template Restructure & Routing

- [x] 2.1 Restructure `templates/legal/terms.html` to place the corporate *Aviso Legal* identity info (Registry data, CIF, address, domain) at the top.
- [x] 2.2 Add the detailed Cookie Policy section outlining cookie classifications (first vs. third-party, session vs. persistent), deletion instructions, browser links, and the 90-day reset guidelines.
- [x] 2.3 Add the Instagram Privacy Policy section detailing `@fastjob.es` profile data access and linking to Instagram's privacy page.
- [x] 2.4 Merge product-specific terms (not an employment agency, "Envíos" credit definition and consumption rules, account suspension disclaimer) into the terms layout.
- [x] 2.5 Add URL routing pattern for `/terms/` in `config/urls.py` pointing to `TermsView`.

## 3. Verification & Testing

- [x] 3.1 Run `pytest apps/core/tests/test_footer.py` to confirm that the existing footer link tests resolve correctly.
- [x] 3.2 Add test assertions to verify that `/privacidad/` and `/terminos/` pages return HTTP 200, contain the text `dpo@basquekide.es`, and include the Google data sharing disclosures.
- [x] 3.3 Add new test cases in `apps/core/tests/test_views.py` verifying that `/privacy/` and `/terms/` paths resolve to HTTP 200.
- [x] 3.4 Execute the test suite using `pytest` to verify that all tests pass.
