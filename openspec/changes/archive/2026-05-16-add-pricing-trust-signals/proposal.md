# Proposal: add-pricing-trust-signals

## Summary
Add a platform-wide "envíos exitosos" trust signal to the pricing page
(`/payments/paquetes/`) to reinforce the purchase decision at the moment
of highest intent — right next to each package price.

## Problem
The pricing page currently shows package names, prices, and feature bullets,
but provides no social proof. Prospective buyers have no signal that the
platform has already delivered real results for other job seekers, which
increases friction at the conversion point.

## Proposed Solution
Inject a single platform-wide successful-send count into the pricing view
and render it as a small green badge inside each card, immediately below the
price line. A secondary trust bar is added at the page footer level to
reinforce the signal after the user has scrolled past the cards.

### Primary placement — inside each price block (lines 26–29 of packages.html)
```html
<div class="mb-6">
  <span class="text-4xl font-extrabold text-gray-900">{{ package.price_eur }}€</span>
  <span class="text-gray-500 text-sm ml-1">/ único pago</span>
  <p class="text-green-600 text-xs font-medium mt-1">
    ✓ +{{ successful_sends_count|intcomma }} envíos exitosos en la plataforma
  </p>
</div>
```

### Secondary placement — page footer trust bar (after line 69)
```html
<p class="text-center text-sm text-gray-500 mt-6">
  ✓ Más de {{ successful_sends_count|intcomma }} envíos completados por
  candidatos reales a través de FastJob
</p>
```

### Data source
`MailingLog.objects.filter(status=MailingLog.Status.SENT).count()` is
computed once per request in the `packages` view and passed as
`successful_sends_count`. No new model, migration, or background task
is required.

## Affected Files
| File | Change |
|------|--------|
| `apps/payments/views.py` | Add `successful_sends_count` to context |
| `templates/payments/packages.html` | Render badge + footer trust bar |
| `apps/mailing/models.py` | Read-only; no change |

## Out of Scope
- Per-package or per-user send counts (no such mapping exists).
- Caching the count query (acceptable at current scale; can be added later).
- A/B testing or feature-flagging the trust signal.
- Any copy changes to the existing feature bullets.

## Risks / Open Questions
- **Zero state**: On a fresh installation the count will be `0`. The badge
  reads "✓ +0 envíos exitosos en la plataforma", which looks odd. The template
  should conditionally hide the badge when the count is zero.
- **Large numbers**: Django's `intcomma` filter (from `django.contrib.humanize`)
  formats `1234` as `1.234` in Spanish locale or `1,234` in English. Confirm
  desired locale formatting before implementation.
