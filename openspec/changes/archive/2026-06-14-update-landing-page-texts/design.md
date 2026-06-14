## Context

The landing page copy needs updates to improve clarity, highlight security and ease of use, and align pricing package details with the new messaging strategy.

## Goals / Non-Goals

**Goals:**
- Update 10 copy/text items on the landing page (`templates/home.html`).
- Update the pricing package feature text on the package cards (`templates/payments/_package_card.html`).
- Ensure no broken layouts or formatting issues are introduced by the changes.

**Non-Goals:**
- Changing any backend Python logic or Celery tasks.
- Modifying database schemas or models.
- Translating pages into other languages.

## Decisions

### Landing Page Edits
All copy updates will be applied directly to the HTML files.
- Modifying lines in `templates/home.html` to replace old Spanish phrases with the updated ones.
- Updating `templates/payments/_package_card.html` to change "Anti-spam Slow-Drip incluido" to "Contacto directo con empresas desde tu propia cuenta de correo".

### Verifying Copy Alignment
- Double-check that item 6 ("Tu CV viaja como adjunto profesional...") is indeed already implemented as requested and requires no changes.

## Risks / Trade-offs

- **Risk**: HTML syntax errors could break formatting.
- **Mitigation**: Verify the landing page compiles and renders correctly.
