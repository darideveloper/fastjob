# Spec Delta: Update Footer Contact Link to Email

## MODIFIED Requirements

### Requirement: Footer links MUST point to the legal and contact pages
The footer in `templates/base.html` SHALL provide functional links to the Privacy Policy, Terms of Service, and a direct contact email. The current placeholders (`#`) MUST be replaced with internal URL names or a direct email link.

- "Privacidad" link MUST point to the URL named `privacy`.
- "Términos" link MUST point to the URL named `terms`.
- "Contacto" link MUST point to `mailto:admin@fastjob.es`.

#### Scenario: Footer contact link is functional
- **WHEN** any page extending `base.html` is rendered
- **THEN** the "Contacto" link has an `href` attribute resolving to `mailto:admin@fastjob.es`
