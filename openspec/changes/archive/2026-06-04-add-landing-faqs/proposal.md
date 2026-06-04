# Proposal: Add FAQs section to Landing Page

## Summary
Add a Frequently Asked Questions (FAQs) section at the bottom of the public landing page, immediately following the pricing teaser and before the footer. This section will feature an engaging title, a brief description, and collapsible cards (accordion style) that reveal the answer when clicked, fully styled to match FastJob's brand guidelines.

## Motivation
Potential users often have common questions about deliverability, pricing, data privacy, and the CV submission process before deciding to purchase a package. Providing immediate answers on the landing page reduces friction, builds trust, and helps drive conversions without requiring the user to navigate away.

## Approach
1. **Data Model**: Create a new `FAQ` model in `apps.core` with fields for `question`, `answer`, `order`, and `is_active`. This allows administrators to manage FAQs (add, edit, reorder, or disable) directly from the Django Admin panel without modifying template code.
2. **Design & Structure**: Add a new `<section id="faqs" class="scroll-mt-20">` to `templates/home.html` right after the `#paquetes` pricing teaser section. The background of this section alternates with the previous section (`bg-brand-soft`) to provide visual rhythm.
3. **Components**: Use native `<details>` and `<summary>` elements to create collapsible FAQ cards. These elements are inherently accessible and require zero JavaScript. The elements are rendered via a loop in the `HomeView` context, fetching active FAQs from the database.
4. **Content Strategy**: Seed the database with the initial 14 FAQ pairs via a data migration (`0004_seed_faqs.py`). This ensures that every environment (development, staging, production) starts with the same consistent base of information.

## Alternatives Considered
- **Static Hardcoding**: Initially considered hardcoding the questions in the template. Rejected because it would require a code deployment for every minor text fix or order change. The dynamic model provides better operational flexibility.
- **Separate FAQ Page**: Adding a separate page requires users to navigate away from the landing page, which could disrupt the conversion funnel.
- **JavaScript Accordion**: Building a custom accordion using JavaScript. Rejected in favor of native `<details>` tags because the native elements are lightweight, performant, and inherently accessible.
