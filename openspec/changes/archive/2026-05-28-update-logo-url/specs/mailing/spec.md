# mailing Specification Delta

## MODIFIED Requirements

### Requirement: SystemSettings Email Branding Fields

`SystemSettings` (`apps/mailing/models.py`) SHALL expose the following fields for configurable email branding:

| Field | Type | Default | verbose_name |
|---|---|---|---|
| `email_logo_url` | `URLField` | `https://raw.githubusercontent.com/darideveloper/fastjob/refs/heads/main/static/images/fastjob-logo.png` | `"URL del logo en emails"` |

#### Scenario: Default branding uses the new URL and Spanish label
- **GIVEN** a freshly seeded database or a system where the admin has not overridden the logo URL.
- **WHEN** a branded email is rendered or the admin panel is viewed.
- **THEN** the logo `<img>` tag MUST point to `https://raw.githubusercontent.com/darideveloper/fastjob/refs/heads/main/static/images/fastjob-logo.png`.
- **AND** the field label in the Django admin MUST be `"URL del logo en emails"`.
