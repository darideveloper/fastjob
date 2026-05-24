# Change: Add scroll-reveal animations and enhanced hover effects across all client-facing pages

## Why

The current site renders all elements statically — content appears instantly with no entrance animation, and interactive elements lack tactile hover feedback beyond basic color transitions. This makes the landing page, pricing page, and dashboard feel flat and static compared to modern SaaS expectations. Adding subtle, accessibility-respecting scroll-reveal animations and polished hover micro-interactions will give the site a dynamic, professional feel that builds credibility and trust with prospective users.

## What Changes

- Add a lightweight IntersectionObserver-based scroll-reveal system (~30 lines of JS, zero dependencies) in `base.html` that removes a `data-reveal` attribute from elements as they enter the viewport, triggering a CSS opacity+transform transition
- Add `[data-reveal]` and variant CSS rules (`static/css/reveal.css`) that start elements invisible/shifted and transition them in when the attribute is removed, with `prefers-reduced-motion` override that keeps elements visible for users who disable animations
- Add staggered delay attributes (`data-reveal-delay="100"`, `data-reveal-delay="200"`, etc.) for grid children (feature cards, trust cards, pricing cards, dashboard stats)
- Add hover micro-interactions to cards, icon containers, and CTAs across: feature cards, trust signal cards, pricing cards, company-finder card, dashboard stat cards, dashboard CV list items, success page checkmark
- All animations use `motion-safe:` Tailwind prefix or `prefers-reduced-motion` media queries to preserve accessibility
- No new third-party dependencies (no AOS, no GSAP, no anime.js) — pure CSS transitions + a tiny IntersectionObserver script

## Impact

- Affected specs: `ui-shell` (6 new requirements: reveal system, hover conventions, landing marking, pricing marking, dashboard marking, auth/status marking). All spec deltas target `ui-shell` because the reveal system is a cross-cutting shell concern and the per-template markings are configurations of that system — they are not modifying the `landing`, `pricing`, or `dashboard` specs themselves.
- Affected code: `templates/base.html` (reveal script + CSS link), new `static/css/reveal.css`, `templates/home.html`, `templates/payments/packages.html`, `templates/payments/success.html`, `templates/dashboard/index.html`, `templates/dashboard/delete_account.html`, `templates/account/login.html`, `templates/404.html`, `templates/500.html`
- Affected assets: `static/css/reveal.css` (new file), `templates/base.html` (additional `<link>` and `<script>`)
- **Ordering dependency**: This change touches the same templates as the active `refresh-landing-shell-and-cv-attachment-copy` change (`home.html`, `packages.html`, `base.html`, `dashboard/index.html`). Apply this change **after** that one to avoid merge conflicts. The `add-auto-upload-cv-on-select` change modifies the CV upload form in `dashboard/index.html` but touches a different section, so there should be no conflict.