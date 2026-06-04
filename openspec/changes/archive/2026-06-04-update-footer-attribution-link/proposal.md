## Why

The current "Powered by" link in the footer points to a WhatsApp contact number. To provide a more professional and comprehensive point of reference for the developer, the link should point to the official developer website.

## What Changes

- Update the attribution link in the footer from a WhatsApp URL to `https://www.darideveloper.com/`.
- Ensure the link text remains "DariDeveloper".
- Maintain existing styling and behavior (new tab, rel="noopener").

## Capabilities

### New Capabilities
- None

### Modified Capabilities
- `ui-shell`: Update the required destination URL for the footer attribution link.

## Impact

- `templates/base.html`: The HTML anchor tag `href` attribute will be updated.
- `openspec/specs/ui-shell/spec.md`: The specification for the footer attribution will be updated to reflect the new URL.
