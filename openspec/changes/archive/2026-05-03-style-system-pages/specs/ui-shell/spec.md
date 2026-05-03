# ui-shell Specification Delta

## ADDED Requirements

### Requirement: Centralized Brand Identity
`templates/base.html` SHALL define the project's brand identity (colors, fonts, and core spacing) within its Tailwind configuration block. Every server-rendered page MUST inherit these settings via template extension. Direct usage of hex codes or hardcoded color classes (e.g., `text-[#4F46E5]`) in app templates is DISCOURAGED in favor of the centralized theme aliases.

#### Scenario: Global color update
- **GIVEN** a requirement to change the brand color from Indigo to Emerald
- **WHEN** the `brand.DEFAULT` value is updated in `templates/base.html`
- **THEN** every page (Home, Dashboard, Login, Logout, 404, etc.) MUST reflect the new color on its interactive elements and accents without further template modifications.

#### Scenario: Error pages follow the global layout
- **GIVEN** a user encounters a 404 or 500 error
- **WHEN** the error template is rendered
- **THEN** it MUST include the standard FastJob navbar and footer
- **AND** the content MUST be centered in a responsive card matching the brand aesthetic.
