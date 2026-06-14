## Context

The legal pages (`/privacidad/` and `/terminos/`) currently display outdated information that does not reference the website owner's legal entity (**FERNANDO PEÑA TORRE**) nor include complete disclosures regarding cookie categories or social media platforms. Additionally, the Google Developer verification team has flagged the Privacy Policy for not explicitly stating how Google user data is shared, transferred, or disclosed, and requires the pages to be accessible at the standard `/privacy` and `/terms` paths.

## Goals / Non-Goals

**Goals:**
- Update `templates/legal/privacy.html` with the consultant's structured tables for Service Contracting and Contacts, retaining specific clauses for DigitalOcean Spaces (5-minute transient links), Stripe transaction data, global blacklisting, and the email `dpo@basquekide.es` for GDPR rights.
- Add an explicit, prominent sub-section in `privacy.html` detailing that Google user data is **not shared, sold, transferred, or disclosed** to any third parties.
- Configure `config/urls.py` to route both `/privacy/` and `/terms/` to their respective views to satisfy Google verification link requirements.
- Update `templates/legal/terms.html` to integrate the Aviso Legal corporate identity, detailed Cookie Policy (classifications, browser instructions), Instagram Privacy Policy, and existing disclaimers (not an employment agency, credit consumption rules, email provider suspension liability).

**Non-Goals:**
- Implementation of a dynamic cookie consent banner component (e.g. Cookiebot/consent manager widget) is out of scope for this task; only the text policy is updated.
- No modifications to database models, views, or database migrations.

## Decisions

### Decision 1: Template-based static implementation
- **Choice**: Maintain static Django template structure in `templates/legal/privacy.html` and `templates/legal/terms.html`.
- **Alternatives**: Store the text in a database table or markdown files parsed dynamically.
- **Rationale**: Static templates are faster, do not require database overhead, and are easy to maintain using standard Django block inheritance (`base.html`).

### Decision 2: Consolidation of legal guidelines and product disclaimers
- **Choice**: Blend the consultant's text with existing technical rules. Specifically:
  - Add the Google User Data Sharing disclosure under the Google API Section.
  - Embed the credit consumption and liability disclaimers under the Terms page layout.
- **Rationale**: Blindly replacing the template contents would break compliance with Google's API verification policy and expose the business to refund/liability disputes.

### Decision 3: URL routing for English paths
- **Choice**: Add secondary paths `privacy/` and `terms/` pointing to `PrivacyView` and `TermsView` in `config/urls.py`, keeping the Spanish paths as well.
- **Alternatives**: Redirect `/privacy/` and `/terms/` to `/privacidad/` and `/terminos/` respectively.
- **Rationale**: While redirection is possible, routing them directly prevents unnecessary redirects for automated validation scripts and ensures immediate resolution for Google review crawlers.

## Risks / Trade-offs

- **[Risk]**: Google Trust & Safety reviews require the Google data sharing disclosures to be clearly visible and accessible.
  - *Mitigation*: Format the Google disclosure section using distinct UI styling (e.g., an alert box or highlighted callout) so it stands out immediately to reviewers.
- **[Risk]**: Overwriting terms text could result in losing detailed product definitions (such as "Envíos" credit consumption).
  - *Mitigation*: Use a structured merge approach in the task list, verifying every existing disclaimer is mapped to a specific section in the new layout.
