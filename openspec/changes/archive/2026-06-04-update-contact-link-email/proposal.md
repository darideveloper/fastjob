# Proposal: Update Footer Contact Link to Email

## Problem
The "Contacto" link in the global footer (defined in `templates/base.html`) is currently a placeholder (`href="#"`). Users who wish to contact support or administration have no direct way to do so via this link.

## Proposed Solution
Modify the "Contacto" link in `templates/base.html` to point to `mailto:admin@fastjob.es`. This provides a direct communication channel for users.

## Scope
- Update `openspec/specs/ui-shell/spec.md` to reflect the functional contact link requirement.
- Modify `templates/base.html` to update the anchor tag's `href` attribute.

## Alternatives Considered
- **Contact Form**: A dedicated contact page with a form. Rejected for now as it adds complexity (view, form, email task) while a simple `mailto:` link satisfies the immediate requirement.
- **Support System**: Integrating a third-party support tool. Rejected as overkill for the current project stage.
