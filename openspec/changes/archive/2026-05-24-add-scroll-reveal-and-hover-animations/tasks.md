## 1. Foundation

- [x] 1.1 Create `static/css/reveal.css` with: `[data-reveal]` initial state (`opacity: 0 !important; transform: translateY(1.5rem) !important`), `[data-reveal="slide-down"]` variant (`transform: translateY(-1.5rem) !important`), `prefers-reduced-motion` override setting `opacity: 1 !important; transform: none !important; transition: none !important` for `[data-reveal]` and all variant selectors, and `@keyframes scale-in` (0% `scale(0)` → 80% `scale(1.1)` → 100% `scale(1)`). The `!important` declarations ensure the hidden state wins over any Tailwind utility regardless of CSS source order.
- [x] 1.2 Add `<link rel="stylesheet" href="{% static 'css/reveal.css' %}">` to `<head>` in `templates/base.html` **before** the Tailwind CDN `<script>` tag to ensure the `[data-reveal]` rules are parsed before any Tailwind-generated utility styles, guaranteeing correct specificity cascade
- [x] 1.3 Add the IntersectionObserver inline `<script>` at the end of `<body>` in `templates/base.html` (before `{% block extra_js %}`): observe all `[data-reveal]` elements with `{ threshold: 0.15 }`, on intersect compute the final delay by looking for a nearest ancestor with `data-reveal-stagger` and multiplying the element's `data-reveal-delay` value by that stagger value, apply the computed `transition-delay` via inline style, then remove `data-reveal` and `data-reveal-delay` and `unobserve`. If no ancestor has `data-reveal-stagger`, treat the delay value as milliseconds directly

## 2. Landing page (`home.html`) — Scroll reveals

- [x] 2.1 Add `data-reveal` + `motion-safe:transition-all motion-safe:duration-700 motion-safe:ease-out` to hero `<h1>`, with `data-reveal-delay="0"`
- [x] 2.2 Add `data-reveal` + transition classes to hero subtitle `<p>`, with `data-reveal-delay="100"`
- [x] 2.3 Add `data-reveal` + transition classes to hero CTA button container `<div>`, with `data-reveal-delay="200"`
- [x] 2.4 Add `data-reveal` + transition classes to Features section `<h2>`, with `data-reveal-delay="0"`
- [x] 2.5 Add `data-reveal` + transition classes + stagger (`data-reveal-delay="0"`, `"100"`, `"200"`, `"300"`) to each of the 4 feature card `<div>` elements
- [x] 2.6 Add `data-reveal` + transition classes to Trust section `<h2>`, with `data-reveal-delay="0"`
- [x] 2.7 Add `data-reveal` + transition classes + stagger (`data-reveal-delay="0"`, `"100"`, `"200"`) to each of the 3 trust card `<div>` elements
- [x] 2.8 Add `data-reveal` + transition classes to Company Finder section `<h2>`, with `data-reveal-delay="0"`
- [x] 2.9 Add `data-reveal` + transition classes to Company Finder subtitle `<p>`, with `data-reveal-delay="100"`
- [x] 2.10 Add `data-reveal` + transition classes to Company Finder filter widget card, with `data-reveal-delay="200"`
- [x] 2.11 Add `data-reveal` + transition classes to Company Finder CTA `<a>`, with `data-reveal-delay="300"`

## 3. Landing page (`home.html`) — Hover effects

- [x] 3.1 Add `group` class + `hover:shadow-md hover:-translate-y-1 motion-safe:transition-all motion-safe:duration-200` to each feature card `<div>`
- [x] 3.2 Add `motion-safe:transition-transform motion-safe:duration-200 group-hover:scale-110` to each feature icon wrapper `<div>` (the `w-14 h-14 bg-brand-muted rounded-2xl` element)
- [x] 3.3 Add `group` class + `hover:shadow-md hover:-translate-y-0.5 motion-safe:transition-all motion-safe:duration-200` to each trust card `<div>`
- [x] 3.4 Add `motion-safe:transition-transform motion-safe:duration-200 group-hover:scale-125` to each trust card "✓" `<div>`
- [x] 3.5 Add `group` class to the Company Finder CTA `<a>` and `motion-safe:transition-transform motion-safe:duration-200 group-hover:translate-x-1` to its arrow `<svg>`

## 4. Pricing page (`packages.html`) — Scroll reveals

- [x] 4.1 Add `data-reveal` + transition classes to the header (h1 + subtitle container), with `data-reveal-delay="0"`
- [x] 4.2 Add `data-reveal` + transition classes to each pricing card `<div>` inside the `{% for %}` loop, using `data-reveal-delay="{{ forloop.counter0 }}"` for stagger. Add `data-reveal-stagger="150"` to the grid wrapper `<div>` (the `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6` element) so the observer computes delays as `forloop.counter0 × 150ms` (0, 150, 300 ms)
- [x] 4.3 Add `data-reveal` + transition classes to the Stripe trust line `<p>`, with `data-reveal-delay="0"`
- [x] 4.4 Add `data-reveal` + transition classes to the social proof line `<p>` (if present), with `data-reveal-delay="100"`
- [x] 4.5 Add `data-reveal` + transition classes to the `{% empty %}` fallback `<div>` (the "No hay paquetes disponibles" card), with `data-reveal-delay="0"`

## 5. Pricing page (`packages.html`) — Hover effects

- [x] 5.1 Add `group` class + `hover:shadow-lg hover:-translate-y-1 motion-safe:transition-all motion-safe:duration-200` to each pricing card `<div>` (except the recommended card which already has `shadow-lg ring-2`; add hover classes there too)
- [x] 5.2 Add `motion-safe:transition-transform motion-safe:duration-150 group-hover:scale-110` to each checkmark `<svg>` inside the feature `<li>` elements (add `group` to each `<li>`)

## 6. Dashboard (`dashboard/index.html`) — Scroll reveals

- [x] 6.1 Add `data-reveal` + transition classes to the pause reason banner (conditional block), with `data-reveal="slide-down" data-reveal-delay="0"`
- [x] 6.2 Add `data-reveal` + transition classes to the dashboard header (h1 + subtitle), with `data-reveal-delay="0"`
- [x] 6.3 Add `data-reveal` + transition classes + stagger (`data-reveal-delay="0"`, `"100"`, `"200"`, `"300"`) to each of the 4 stat card `<div>` elements
- [x] 6.4 Add `data-reveal` + transition classes to the CV list card, with `data-reveal-delay="0"`
- [x] 6.5 Add `data-reveal` + transition classes to the Filters card, with `data-reveal-delay="100"`
- [x] 6.6 Add `data-reveal` + transition classes to the Danger zone card, with `data-reveal-delay="200"`
- [x] 6.7 Add `data-reveal` + transition classes to the Recent activity card, with `data-reveal-delay="0"`

## 7. Dashboard (`dashboard/index.html`) — Hover effects

- [x] 7.1 Add `hover:shadow-md hover:border-brand/20 motion-safe:transition-all motion-safe:duration-200` to each of the 4 stat card `<div>` elements

## 8. Login page (`account/login.html`) — Scroll reveal

- [x] 8.1 Add `data-reveal` + `motion-safe:transition-all motion-safe:duration-500 motion-safe:ease-out` to the login card container `<div>`, with `data-reveal-delay="0"`

## 8b. Delete account page (`dashboard/delete_account.html`) — Scroll reveal

- [x] 8b.1 Add `data-reveal` + `motion-safe:transition-all motion-safe:duration-500 motion-safe:ease-out` to the card container `<div>` (the `bg-white border border-red-200 rounded-2xl` div), with `data-reveal-delay="0"`

## 9. Payment success page (`payments/success.html`) — Animations

- [x] 9.1 Add `data-reveal` + `motion-safe:transition-all motion-safe:duration-500 motion-safe:ease-out data-reveal-delay="150"` to the h1
- [x] 9.2 Add `data-reveal` + transition classes + `data-reveal-delay="300"` to the credits number paragraph
- [x] 9.3 Add `data-reveal` + transition classes + `data-reveal-delay="450"` to the CTA `<a>`
- [x] 9.4 Add `motion-safe:animate-[scale-in_0.4s_ease-out]` class to the checkmark wrapper `<div>` (the `w-20 h-20 bg-green-100 rounded-full` div), and define the `scale-in` keyframe in `reveal.css`. Fallback: if Tailwind CDN does not correctly parse the arbitrary `animate-[...]` class, add a `.reveal-checkmark` class in `reveal.css` with `animation: scale-in 0.4s ease-out` and use `motion-safe:reveal-checkmark` instead

## 10. Error pages (404, 500)

- [x] 10.1 Add `data-reveal` + `motion-safe:transition-all motion-safe:duration-500 motion-safe:ease-out` to the card container `<div>` in `templates/404.html`
- [x] 10.2 Add `data-reveal` + transition classes to the card container `<div>` in `templates/500.html`

## 11. Verification

- [x] 11.1 Load `/` (landing) at 1440px and scroll — verify all sections reveal with stagger and no layout shift
- [x] 11.2 Load `/payments/paquetes/` — verify pricing cards stagger in and hover lifts work
- [x] 11.3 Load `/dashboard/` (authenticated) — verify stat cards stagger and hover shadow appears
- [x] 11.4 Load `/accounts/login/` — verify card fades in
- [x] 11.5 Load `/payments/success/` — verify checkmark scales in and subsequent elements reveal
- [x] 11.6 Enable `prefers-reduced-motion: reduce` in browser dev tools and reload all pages — verify NO elements are invisible and NO transforms are applied
- [x] 11.7 Test at 320px viewport — verify no horizontal overflow on any page
- [x] 11.8 Test at 768px and 1440px — verify animations trigger appropriately and hover effects work
- [x] 11.9 Verify `reveal.css` specificity: confirm that `[data-reveal]` hidden state (opacity: 0) wins over any Tailwind utility class regardless of CSS load order, by temporarily moving the `<link>` tag after the Tailwind `<script>` and confirming `[data-reveal]` still hides elements