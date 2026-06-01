# Tasks: Add Legal Pages

## 1. Views and URLs
- [x] 1.1 Add `PrivacyView` and `TermsView` to `apps/core/views.py` using `TemplateView`.
- [x] 1.2 Update `config/urls.py` to include `/privacidad/` and `/terminos/` paths with names `privacy` and `terms`.

## 2. Templates Creation
- [x] 2.1 Create `templates/legal/privacy.html`.
  - [x] Extend `base.html`.
  - [x] Include sections: Introduction, Data Collected (OAuth, CVs, Payments), Purpose, Third Parties, Your Rights, and Security.
- [x] 2.2 Create `templates/legal/terms.html`.
  - [x] Extend `base.html`.
  - [x] Include sections: Acceptance, Service Description, Credits/Envíos, User Responsibilities, Termination, and Liability.

## 3. UI Integration
- [x] 3.1 Update `templates/base.html` footer.
  - [x] Replace `href="#"` with `{% url 'privacy' %}` for the "Privacidad" link.
  - [x] Replace `href="#"` with `{% url 'terms' %}` for the "Términos" link.

## 4. Validation
- [x] 4.1 Verify that both pages are accessible and render correctly with the global layout.
- [x] 4.2 Verify that the footer links navigate to the correct pages.
- [x] 4.3 Ensure no horizontal overflow on mobile viewports for the new pages.
