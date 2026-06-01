# Proposal: Add Legal Pages (Privacy Policy and Terms of Service)

## Summary
Implement the Privacy Policy and Terms of Service pages to ensure legal compliance for data collection and service usage. These pages will explicitly cover the project's core integrations: Google/Microsoft OAuth, DigitalOcean Spaces for CV hosting, and Stripe for payments.

## Motivation
The project currently uses placeholders (`#`) in the footer for "Privacidad" and "Términos". As the app processes sensitive user data (OAuth tokens and CV documents) and handles financial transactions, it is critical to have clear legal terms that define data processing, user responsibilities, and service limitations.

## Proposed Changes
### Core Application (`apps/core`)
- Add `PrivacyView` and `TermsView` as `TemplateView` subclasses in `apps/core/views.py`.
- Map `/privacidad/` and `/terminos/` in `config/urls.py`.

### Templates
- Create `templates/legal/privacy.html` with detailed sections on data collection, OAuth permissions, CV storage, and third-party processors.
  - **Include mandatory Google Limited Use disclosure** for the `gmail.modify` scope.
  - **Disclose the global nature of the unsubscribe/blacklist system**.
  - **Include a section on functional cookies** (Django sessions/CSRF).
- Create `templates/legal/terms.html` with rules on service usage, credits/envíos, and liability disclaimers.
  - **Ensure consistent use of "Envíos" terminology**.
- Update `templates/base.html` footer to replace `#` with `{% url 'privacy' %}` and `{% url 'terms' %}`.

## Design Decisions
- **Static Templates**: Using Django templates for legal content is the most straightforward approach, avoiding unnecessary database complexity for content that is rarely updated.
- **Language**: The content will be in Spanish, matching the project's primary language.
- **Scope-Specific Content**: The policies will explicitly mention Google and Microsoft OAuth scopes, Stripe for payments, and the "slow-drip" mailing engine logic to provide full transparency.

## Related Capabilities
- **ui-shell**: Updates the global footer.
- **landing**: Adds public legal visibility.
