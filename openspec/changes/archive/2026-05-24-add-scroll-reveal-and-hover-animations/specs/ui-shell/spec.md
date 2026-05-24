## ADDED Requirements

### Requirement: Scroll-Reveal Animation System

All final-user pages that extend `templates/base.html` SHALL support a scroll-reveal animation system implemented as a zero-dependency IntersectionObserver script embedded in `base.html` and a companion CSS file `static/css/reveal.css`. Elements marked with `data-reveal` SHALL start invisible (`opacity: 0 !important; transform: translateY(1.5rem) !important`) and transition to their natural position when the observer detects they have entered the viewport at 15 % visibility. The `!important` declarations are required to guarantee that the initial hidden state wins over any Tailwind utility classes on the same element, regardless of CSS source order. The observer SHALL remove the `data-reveal` attribute on reveal, apply any `transition-delay` from a `data-reveal-delay` attribute, and then unobserve the element.

For elements inside Django `{% for %}` loops (e.g. pricing cards), the `data-reveal-delay` SHALL use `forloop.counter0` multiplied by a stagger interval defined on a parent wrapper via `data-reveal-stagger` (e.g. `data-reveal-stagger="150"`). The observer script SHALL look for the nearest ancestor with `data-reveal-stagger` and compute the final delay as `value * stagger`.

Users who have enabled `prefers-reduced-motion: reduce` in their OS or browser settings SHALL see all elements rendered in their final state immediately (no opacity transition, no transform shift, no stagger delay), via a `@media (prefers-reduced-motion: reduce)` override in `reveal.css`. This override SHALL also include `transition: none !important` to suppress any inherited or inline transitions that might otherwise produce a visible shift.

The `reveal.css` file SHALL also define a `"slide-down"` reveal variant (`[data-reveal="slide-down"] { transform: translateY(-1.5rem) !important }`) for elements that should appear to slide downward into position (e.g. top banners), and a `"scale-in"` keyframe animation (`0% { transform: scale(0) } 80% { transform: scale(1.1) } 100% { transform: scale(1) }`) for celebratory icons (e.g. the success-page checkmark).

#### Scenario: Element fades and slides up on scroll

- **GIVEN** an element with `data-reveal` and `motion-safe:transition-all motion-safe:duration-700 motion-safe:ease-out` classes exists below the fold
- **WHEN** the user scrolls the element into the viewport (15 % visible)
- **THEN** the `data-reveal` attribute is removed
- **AND** the element transitions from `opacity: 0; transform: translateY(1.5rem)` to `opacity: 1; transform: none` over 700 ms

#### Scenario: Staggered sibling reveals with delay

- **GIVEN** four elements with `data-reveal` and `data-reveal-delay` values `"0"`, `"1"`, `"2"`, `"3"` inside a container with `data-reveal-stagger="100"`
- **WHEN** all four enter the viewport simultaneously
- **THEN** the first element reveals immediately (0 × 100 ms = 0 ms delay)
- **AND** the second, third, and fourth elements begin their transitions 100 ms, 200 ms, and 300 ms after the first respectively (computed as delay × stagger)

#### Scenario: Stagger in Django for-loop with forloop.counter0

- **GIVEN** a Django `{% for package in packages %}` loop where each card has `data-reveal-delay="{{ forloop.counter0 }}"` and the grid wrapper has `data-reveal-stagger="150"`
- **WHEN** three cards enter the viewport simultaneously
- **THEN** the cards reveal with delays of 0 ms, 150 ms, and 300 ms respectively

#### Scenario: Reduced-motion user sees no animation

- **GIVEN** a user whose browser reports `prefers-reduced-motion: reduce`
- **WHEN** any page with `data-reveal` elements is loaded
- **THEN** all elements render at `opacity: 1; transform: none` immediately
- **AND** no transitions are applied (`transition: none !important`)
- **AND** the IntersectionObserver still runs (removing attributes) but no visual transition occurs

#### Scenario: Slide-down banner reveal

- **GIVEN** a conditional banner element with `data-reveal="slide-down"`
- **WHEN** the element enters the viewport
- **THEN** it transitions from `opacity: 0; transform: translateY(-1.5rem)` to `opacity: 1; transform: none`

#### Scenario: No new third-party JavaScript or CSS dependencies

- **WHEN** the rendered HTML of any page extending `base.html` is inspected
- **THEN** the only third-party `<script src=…>` tags are those that existed before this change (Tailwind CDN, combobox.js)
- **AND** no `<script>` tag loads AOS, GSAP, anime.js, or any other animation library

### Requirement: Hover Micro-Interactions on Cards and Icons

Interactive card elements and icon containers across all final-user pages SHALL provide subtle hover feedback using only Tailwind utility classes with the `motion-safe:` prefix. Cards SHALL lift (`hover:-translate-y-0.5` or `hover:-translate-y-1`) and gain enhanced shadow (`hover:shadow-md` or `hover:shadow-lg`) on hover. Icon wrappers inside grouped cards SHALL scale up (`group-hover:scale-110` or `group-hover:scale-125`) on card hover. Arrow icons inside grouped CTA links SHALL shift right (`group-hover:translate-x-1`) on link hover.

All hover transitions SHALL use `motion-safe:transition-all motion-safe:duration-200` (or `motion-safe:duration-150` for icons) and SHALL be suppressed entirely under `prefers-reduced-motion: reduce`.

#### Scenario: Feature card lifts on hover

- **GIVEN** an anonymous visitor on the landing page
- **WHEN** the user hovers over any of the four "Cómo funciona" feature card `<div>` elements
- **THEN** the card visually shifts upward by 1 px (Tailwind `hover:-translate-y-1`) and its shadow increases
- **AND** hovering the card also scales the icon wrapper inside it by 10 %

#### Scenario: Pricing card lifts on hover

- **GIVEN** an anonymous visitor on the pricing page
- **WHEN** the user hovers over any pricing card (including the "Recomendado" card)
- **THEN** the card shifts upward (`hover:-translate-y-1`) and its shadow increases to `shadow-lg`
- **AND** the "Recomendado" ring is preserved during the hover

#### Scenario: Dashboard stat card shows subtle hover

- **GIVEN** an authenticated user on the dashboard
- **WHEN** the user hovers over any of the four stat cards
- **THEN** the card gains `shadow-md` and a subtle border-color shift (`hover:border-brand/20`)
- **AND** no card lifts more than 0.5 rem

#### Scenario: Hover effects respect reduced motion

- **GIVEN** a user whose browser reports `prefers-reduced-motion: reduce`
- **WHEN** they hover over any card or icon with `motion-safe:transition-*` and `hover:*` classes
- **THEN** the hover state change (shadow, color) still occurs instantly
- **AND** no `transform` property is applied (no lift, no scale)

### Requirement: Landing Page Scroll-Reveal Marking

The landing page (`templates/home.html`) SHALL mark the following elements with `data-reveal` (and stagger delays per the design document) so they animate into view on scroll: hero headline, hero subtitle, hero CTA row, Features section heading, each of the four feature cards, Trust section heading, each of the three trust cards, Company Finder section heading, Company Finder subtitle, Company Finder filter card, and Company Finder CTA button. All marked elements SHALL also carry `motion-safe:transition-all motion-safe:duration-700 motion-safe:ease-out` (or `motion-safe:duration-500` for smaller elements) to define the transition timing.

#### Scenario: Hero section reveals in sequence

- **GIVEN** an anonymous visitor scrolls to the landing page
- **WHEN** the hero section enters the viewport
- **THEN** the `<h1>` reveals with 0 ms delay
- **AND** the subtitle `<p>` reveals 100 ms after the headline
- **AND** the CTA button row reveals 200 ms after the headline

#### Scenario: Feature cards stagger on scroll

- **GIVEN** the four "Cómo funciona" feature cards are below the fold
- **WHEN** they scroll into view
- **THEN** each card reveals 100 ms after the previous one (delays of 0, 100, 200, 300 ms)

#### Scenario: Trust cards stagger on scroll

- **GIVEN** the three trust-signal cards are below the fold
- **WHEN** they scroll into view
- **THEN** each card reveals 100 ms after the previous one (delays of 0, 100, 200 ms)

### Requirement: Pricing Page Scroll-Reveal Marking

The pricing page (`templates/payments/packages.html`) SHALL mark the following elements with `data-reveal`: the header (h1 + subtitle container), the pricing grid wrapper with `data-reveal-stagger="150"` so that each pricing card in the `{% for %}` loop can use `data-reveal-delay="{{ forloop.counter0 }}"` to compute stagger delays of 0, 150, and 300 ms, the Stripe trust line, and the social proof line.

#### Scenario: Pricing cards stagger on scroll

- **GIVEN** an anonymous visitor scrolls to the pricing page
- **WHEN** the pricing grid enters the viewport
- **THEN** the first pricing card reveals with 0 ms delay
- **AND** the second pricing card reveals 150 ms later
- **AND** the third pricing card reveals 300 ms later
- **AND** the stagger is computed from `data-reveal-delay="{{ forloop.counter0 }}"` multiplied by the parent's `data-reveal-stagger="150"`

### Requirement: Dashboard Scroll-Reveal Marking

The dashboard page (`templates/dashboard/index.html`) SHALL mark the following elements with `data-reveal`: the pause-reason banner (with `data-reveal="slide-down"` variant), the dashboard header, each of the four stat cards (with stagger delays 0, 100, 200, 300 ms), the CV list card, the filters card, the danger-zone card, and the recent-activity card. Dashboard stat card transitions SHALL use `motion-safe:duration-500` (faster than landing, since the dashboard is functional not marketing).

#### Scenario: Dashboard stat cards stagger on load

- **GIVEN** an authenticated user loads the dashboard
- **WHEN** the page renders
- **THEN** the four stat cards reveal in sequence with 100 ms stagger

#### Scenario: Pause banner slides down

- **GIVEN** an authenticated user whose campaign is paused for a quota reason
- **WHEN** the dashboard renders with the pause banner visible
- **THEN** the banner reveals using the `slide-down` variant (entering from above)

### Requirement: Auth and Status Page Scroll-Reveal Marking

The login page (`templates/account/login.html`) SHALL mark its card container with `data-reveal`. The delete-account page (`templates/dashboard/delete_account.html`) SHALL mark its card container with `data-reveal`. The payment success page (`templates/payments/success.html`) SHALL mark its checkmark icon with the `scale-in` keyframe animation, and its h1, credits number, and CTA button with `data-reveal` at staggered delays (150 ms, 300 ms, 450 ms). The 404 and 500 error pages SHALL mark their card containers with `data-reveal`.

#### Scenario: Success page checkmark bounces in

- **GIVEN** an authenticated user who just completed a payment
- **WHEN** the success page loads
- **THEN** the green checkmark icon plays the `scale-in` keyframe animation
- **AND** the "¡Pago completado!" headline reveals 150 ms after the checkmark
- **AND** the credits number reveals 300 ms after the checkmark
- **AND** the CTA button reveals 450 ms after the checkmark

#### Scenario: Login card fades in

- **GIVEN** an anonymous visitor navigates to `/accounts/login/`
- **WHEN** the page renders
- **THEN** the login card container fades up into view with `duration-500`

#### Scenario: Error page card fades in

- **GIVEN** a visitor encounters a 404 or 500 error
- **WHEN** the error page renders
- **THEN** the centered card container fades up into view

#### Scenario: Delete-account card fades in

- **GIVEN** an authenticated user navigates to `/dashboard/delete-account/`
- **WHEN** the page renders
- **THEN** the danger-zone card container fades up into view with `duration-500`