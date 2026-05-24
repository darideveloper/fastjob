# Change: Fix footer social links alignment on desktop

## Why
On desktop viewports (`sm+`), the Instagram icon in the footer sits in the middle of three equally-spaced columns (copyright | social | legal), but the design intent is for the social icon to align to the right alongside the legal links.

## What Changes
- Move the social-links `<div>` into the same flex container as the legal links so the right side contains Instagram + legal links
- Simplify the left side to just the copyright `<span>` (no wrapper)
- Preserve the mobile `< sm` vertical stacking unchanged
- Update the `ui-shell` spec to reflect the new desktop layout

## Impact
- Affected code: `templates/base.html` (footer block, ~3 lines restructured)
- Affected spec: `ui-shell` (MODIFIED requirement: "Footer renders a scalable social-links cluster", layout scenario updated)
- No new dependencies, no JS changes, no data changes
