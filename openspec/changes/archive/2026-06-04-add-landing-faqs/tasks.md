## 1. Scaffold FAQ Section Layout

- [x] 1.1 In `templates/home.html`, insert a `<section id="faqs" class="py-20 bg-white scroll-mt-20">` below the `#paquetes` section
- [x] 1.2 Add a container (`max-w-screen-2xl mx-auto px-4 sm:px-6 lg:px-8`) with the section title "Preguntas Frecuentes" using `text-wrap: balance`
- [x] 1.3 Validate by opening the dev server and verifying the new section renders at the bottom and anchor links (e.g., `/#faqs`) scroll with top margin

## 2. Implement Accessible FAQ Accordion Component

- [x] 2.1 Create `<details>` and `<summary>` elements with Tailwind classes (`group bg-white border border-brand-muted rounded-2xl p-6 mb-4 shadow-sm`)
- [x] 2.2 Add unique `id` attributes to each `<details>` element (e.g., `faq-deliverability`)
- [x] 2.3 Add focus ring utility to `<summary>`: `focus-visible:ring-2 focus-visible:ring-accent outline-none`
- [x] 2.4 Add an SVG chevron icon inside `<summary>` with `aria-hidden="true"`
- [x] 2.5 Animate chevron (`group-open:rotate-180 transition-transform duration-200 motion-reduce:transition-none`) and hide default marker (`list-none [&::-webkit-details-marker]:hidden`)
- [x] 2.6 Validate keyboard navigation (Tab/Enter), focus ring visibility, and deep-linking to specific FAQ IDs

## 3. Populate FAQ Content (Dynamic)

- [x] 3.1 Create `FAQ` model in `apps/core/models.py` with question, answer, order, and is_active fields
- [x] 3.2 Create and apply migrations, including a seed migration with the 14 QA pairs
- [x] 3.3 Update `apps/core/views.py:HomeView` to fetch active FAQs and pass them to the context
- [x] 3.4 Refactor `templates/home.html` to render FAQs using a loop and handle the empty state
- [x] 3.5 Register `FAQ` model in Django admin
- [x] 3.6 Validate that the dynamic rendering matches the previous static design
