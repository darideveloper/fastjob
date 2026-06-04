## Why

The current Instagram link in the footer points to `https://instagram.com/joinfastjob`, which was a dummy handle. The official Instagram account for FastJob is now `https://www.instagram.com/fastjob.es`. Updating this link ensures users are directed to the correct social media profile.

## What Changes

- Update the Instagram URL in the `social_links` context processor.
- Update the Instagram URL in the UI Shell specification to reflect the official link.

## Capabilities

### New Capabilities
- None

### Modified Capabilities
- `ui-shell`: Updating the Instagram URL requirement to `https://www.instagram.com/fastjob.es` and updating the `aria_label` if necessary to match the official handle or branding.

## Impact

- `apps/core/context_processors.py`: The `url` and potentially `aria_label` in the `social_links` function.
- `openspec/specs/ui-shell/spec.md`: The requirement for the Instagram link URL.
- Footer component: Will now render the correct link.
