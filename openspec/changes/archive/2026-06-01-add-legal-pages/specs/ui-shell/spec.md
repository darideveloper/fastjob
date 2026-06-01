# ui-shell Specification (Delta)

## ADDED Requirements

### Requirement: Footer links MUST point to the legal pages
The footer in `templates/base.html` SHALL provide functional links to the Privacy Policy and Terms of Service pages. The current placeholders (`#`) MUST be replaced with internal URL names.

- "Privacidad" link MUST point to the URL named `privacy`.
- "Términos" link MUST point to the URL named `terms`.

#### Scenario: Footer links are functional
- **WHEN** any page extending `base.html` is rendered
- **THEN** the "Privacidad" link has an `href` attribute resolving to `/privacidad/`
- **AND** the "Términos" link has an `href` attribute resolving to `/terminos/`
