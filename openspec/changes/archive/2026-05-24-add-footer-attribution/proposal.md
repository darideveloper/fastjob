# Change: Add footer attribution line for DariDeveloper

## Why
The footer should display a small attribution credit: "Powered by DariDeveloper" with a WhatsApp contact link, to acknowledge the developer behind the project.

## What Changes
- Add a small `<p>` line beneath the existing copyright text in `templates/base.html` footer, reading `Powered by <a href="…">DariDeveloper</a>`
- The attribution MUST use `text-xs text-gray-400` — strictly **smaller** than the copyright's `text-sm text-gray-500` — and sit on its own line below the copyright `<span>` with no top gap or minimal spacing
- The link MUST point to `https://api.whatsapp.com/send?phone=5214493402622` with `target="_blank` and `rel="noopener"`
- The existing footer layout (copyright + social left, legal right on desktop; vertical stack on mobile) MUST remain intact

## Impact
- Affected code: `templates/base.html` (footer block, ~2–3 lines added)
- Affected spec: `ui-shell` (ADDED requirement for footer attribution)
- No new dependencies, no JS changes, no data changes, no context processor changes
