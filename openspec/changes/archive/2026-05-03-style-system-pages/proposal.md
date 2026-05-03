# Proposal: Style System Pages

## Why
Several user-facing pages (logout confirmation, social signup, 404, 500) render as plain, unstyled HTML because they use default library or framework templates. This breaks the visual brand identity of FastJob and provides a poor user experience.

## What Changes
Create custom Django templates to override the default unstyled pages. These templates will extend `templates/base.html` to inherit the global navigation, footer, and Tailwind CSS configuration. We will also consolidate branding variables in `base.html` to allow for easy global theme updates.

- **django-allauth**: Create custom templates for `logout`, `social signup`, `social connections`, `social cancelled`, and `social error`.
- **Error Pages**: Create custom `404.html` and `500.html` templates.
- **Theming**: Refactor `base.html` to centralize color and font definitions.

## Risks & Mitigations
- **Template Fragment Drift**: If `allauth` changes its internal template context, our overrides might break. *Mitigation: Keep templates simple, focusing on layout and using standard `allauth` form tags.*
- **Production Errors**: 500 pages must be extremely robust. *Mitigation: Ensure the 500 template has minimal logic and handles its own errors gracefully.*
