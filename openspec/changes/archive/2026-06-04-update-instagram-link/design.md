## Context

The FastJob Instagram handle has been finalized as `fastjob.es`. The current project uses a placeholder handle `joinfastjob` in the footer social links.

## Goals / Non-Goals

**Goals:**
- Update the Instagram URL to `https://www.instagram.com/fastjob.es`.
- Ensure the `aria-label` correctly reflects the brand.

**Non-Goals:**
- Changing the SVG icon for Instagram.
- Adding new social media links.
- Changing the layout of the footer.

## Decisions

### Update Context Processor
The `social_links` context processor in `apps/core/context_processors.py` is the single source of truth for social links used in templates.
- **Decision:** Update the `url` value to `https://www.instagram.com/fastjob.es`.
- **Decision:** Update the `aria_label` to `FastJob en Instagram`. (This remains consistent but is confirmed as correct).

### Update Specs
The `ui-shell` spec defines the footer content requirements.
- **Decision:** Create a delta spec for `ui-shell` to reflect the new URL requirement.

## Risks / Trade-offs

- **[Risk]** Broken link if the URL is mistyped. → **Mitigation**: Double-check the URL and verify in the browser.
- **[Risk]** Divergence between code and spec. → **Mitigation**: Update both the context processor and the OpenSpec documentation.
