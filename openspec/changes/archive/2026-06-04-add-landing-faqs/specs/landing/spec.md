# landing Specification Deltas

## MODIFIED Requirements

### Requirement: Landing page renders a FAQs section at the bottom

The public landing page (`templates/home.html`) SHALL render a Frequently Asked Questions (FAQs) section as its **final** in-content section, positioned immediately after the pricing teaser section (`#paquetes`) and before the page footer.

The section MUST include:
- A clear heading (e.g., "Preguntas frecuentes").
- A brief descriptive subtitle.
- A list of collapsible FAQ cards containing static questions and answers about the product.

The FAQ cards MUST be implemented using semantic HTML `<details>` and `<summary>` elements to ensure native accessibility, keyboard navigation, and zero-JavaScript operation. The cards MUST be styled using the project's Tailwind CSS utilities to match the brand identity (e.g., `bg-white`, `rounded-2xl`, `border-brand-muted`). The `<summary>` element MUST display an indicator (like a chevron or plus/minus icon) that visually reflects the expanded/collapsed state using CSS (e.g., via `group-open` modifier in Tailwind).

**New Specifications:**
- Each FAQ item MUST have a unique `id` attribute (e.g., `id="faq-segmento"`) to support deep-linking.
- The section container MUST have `scroll-margin-top` (e.g., `scroll-mt-20`) to ensure anchor navigation does not hide the section behind fixed headers.
- The disclosure indicator MUST be hidden from assistive technologies using `aria-hidden="true"`.
- Typography MUST use balanced wrapping (`text-wrap: balance` or `text-pretty`) on headings and proper curly quotes (`“ ”`) for text.
- Animations MUST respect the `prefers-reduced-motion` media query.

#### Scenario: FAQs section appears after the pricing teaser
- **WHEN** an anonymous or authenticated visitor loads `/`
- **THEN** the rendered HTML contains a `<section>` with `id="faqs"` and `scroll-mt-20`
- **AND** the section is placed after the `#paquetes` section and before the end of the `content` block

#### Scenario: FAQs are natively collapsible and accessible
- **WHEN** the visitor scrolls to the FAQs section
- **THEN** the FAQ items are rendered as `<details>` elements with unique IDs
- **AND** the question text is wrapped in a `<summary>` element with visible focus states
- **AND** clicking the `<summary>` expands the card to reveal the answer text
- **AND** the component operates fully without any custom JavaScript

#### Scenario: FAQ cards align with the brand style
- **WHEN** the FAQs section is rendered
- **THEN** the individual FAQ cards have a border (`border-brand-muted`) and rounded corners (`rounded-2xl` or similar)
- **AND** an icon or chevron indicates whether the card is open or closed and is hidden from ARIA
