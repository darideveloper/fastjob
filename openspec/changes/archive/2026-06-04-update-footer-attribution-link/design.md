## Context

The project footer currently contains a developer attribution link pointing to a WhatsApp number. The developer wants to redirect this traffic to their official professional website.

## Goals / Non-Goals

**Goals:**
- Update the `href` attribute of the attribution link in `templates/base.html`.
- Update the relevant requirement in `openspec/specs/ui-shell/spec.md` to maintain documentation consistency.

**Non-Goals:**
- Changing the visual style, position, or text of the attribution.
- Modifying other footer links (social, legal).

## Decisions

- **Direct replacement**: The URL will be replaced directly in the template. No dynamic setting or context processor is needed for this static attribution as it is considered a core part of the template's branding.

## Risks / Trade-offs

- [Risk] Broken link if the website URL is mistyped → [Mitigation] Manual verification of the link after deployment.
