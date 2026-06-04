# Design: Add FAQs section to Landing Page

## Problem Statement
Users visiting the landing page often have repeating questions about how the service works, data privacy, and deliverability. Currently, there is no central place on the home page to address these, which may lead to drop-offs in the conversion funnel.

## Proposed Solution
Implement a "Preguntas frecuentes" (FAQ) section using a vertically stacked accordion design. The accordion will leverage native HTML `<details>` and `<summary>` elements for maximum performance and accessibility without requiring client-side JavaScript.

## Architectural Decisions

### 1. Native Accordion (No-JS)
We will use `<details>` and `<summary>` instead of a custom JavaScript component.
- **Rationale**: Minimal bundle size, better performance, and inherent accessibility support (ARIA roles and keyboard interaction are handled by the browser).
- **Styling**: Tailwind's `group-open:` modifier will be used to animate the disclosure chevron and adjust card borders.

### 2. Dynamic Content Strategy (Updated)
FAQ content is stored in a `FAQ` Django model (`apps.core.models.FAQ`).
- **Rationale**: While content is relatively static, storing it in the database allows for easy updates via the Django admin without code changes.
- **Scale**: The implementation includes a seed migration populating the 14 specific FAQ items provided by the user.
- **Rendering**: `HomeView` fetches active FAQs ordered by an `order` field and the template renders them via a `{% for %}` loop.

### 3. Anchor Linking and Deep-linking
Each FAQ card will have a unique `id` based on its topic (e.g., `faq-que-es`, `faq-rebotes`, `faq-seguridad`).
- **Rationale**: This allows marketing links or support to point users to specific answers (e.g., `fastjob.es/#faq-deliverability`). The section itself will have `scroll-mt-20` to prevent being hidden by the fixed header.

## Visual Design
- **Container**: `max-w-3xl mx-auto` for optimal reading line length.
- **Card Styling**: `bg-white`, `border-brand-muted`, `rounded-2xl`, `p-6`.
- **States**: 
  - **Hover**: Subtle shadow increase.
  - **Focus**: `focus-visible:ring-2` on the `<summary>` element.
  - **Open**: Border color change or inner padding adjustment.

## Copywriting & Accuracy
- **Discrepancy Note**: The technical documentation (`project.md`) mentions "links over attachments," but the implementation and current landing copy refer to "PDF attachments." The FAQ content must align with the current implementation (attachments) while this discrepancy is resolved.
