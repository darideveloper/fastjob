# Change: Move filters section to second position on landing page

## Why
The company-finder (filters) section is currently the 4th section on the landing page, after the hero, features ("¿Cómo funciona?"), and trust signals. Moving it to the 2nd position — immediately after the hero — gives visitors instant access to the interactive filter tool, increasing engagement before they see the informational sections below.

## What Changes
- Move the `<!-- Company Finder -->` `<section>` in `templates/home.html` from position 4 to position 2 (directly after the hero)
- Move the `<!-- Features -->` and `<!-- Trust Signals -->` sections down to positions 3 and 4 respectively
- Change the `<!-- Features -->` section background from transparent/white to `bg-gray-50` to maintain visual separation from the Company Finder section above it (both would otherwise share a white background with no visual break)
- Update the "Public Company-Finder Section on Landing Page" requirement to reflect the new position: "immediately below the hero section" instead of "above the call-to-action that links to the pricing/packages page"
- Update the "Landing page renders a pricing-teaser section at the bottom" requirement to remove the claim that the pricing teaser is "positioned immediately below the existing company-finder section" — it will now be below the trust-signals section

## Impact
- Affected specs: `landing`
- Affected code: `templates/home.html` (section reordering + one background class change on the Features section)

## Visual Rhythm Note
The current layout alternates backgrounds cleanly: dark gradient → white → `bg-brand-soft` → `bg-white` → `bg-brand-soft`. After the reorder, sections 2 and 3 (Company Finder `bg-white` and Features transparent/white) would share the same background with no visual break, as would sections 4 and 5 (`bg-brand-soft` × 2). Changing Features to `bg-gray-50` restores a distinguishable rhythm: dark → white → light gray → brand-soft → brand-soft.