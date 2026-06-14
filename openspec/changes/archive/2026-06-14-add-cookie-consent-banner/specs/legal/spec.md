## ADDED Requirements

### Requirement: Interactive Cookie Consent Banner
The application SHALL display a Cookie Consent Banner to first-time or un-consented visitors on any public page.
The banner SHALL support three main actions:
1. **Aceptar todo (Accept All):** Grants consent to all cookie categories (Technical, Analytics, Personalization, and Advertising).
2. **Rechazar todo (Reject All):** Rejects all optional categories, retaining only the Technical/Essential category.
3. **Personalizar (Customize):** Displays a configuration panel with granular toggles for each category.

The Technical/Essential toggle SHALL be disabled and permanently set to active. The other toggles (Analytics, Personalization, Advertising) SHALL default to inactive.

The user's consent status SHALL be stored locally in the browser (via `localStorage` or a local cookie) to prevent the banner from showing up again on subsequent visits.

#### Scenario: Anonymous user visits the site and accepts all cookies
- **GIVEN** an anonymous visitor who has not set cookie preferences
- **WHEN** they load the landing page
- **THEN** the Cookie Consent Banner is visible at the bottom of the page
- **WHEN** the user clicks "Aceptar todo"
- **THEN** the banner is dismissed
- **AND** all cookie category consents are saved as `true` in local storage
- **AND** the banner does not reappear on reload

#### Scenario: Anonymous user customizes cookie consent
- **GIVEN** an anonymous visitor who has not set cookie preferences
- **WHEN** they load the landing page
- **THEN** the Cookie Consent Banner is visible
- **WHEN** the user clicks "Personalizar"
- **THEN** the customization panel reveals toggles for Technical, Analytics, Personalization, and Advertising
- **AND** the Technical toggle is active and locked (cannot be disabled)
- **AND** other toggles are inactive by default
- **WHEN** the user activates "Analytics" and clicks "Guardar preferencias"
- **THEN** the banner is dismissed
- **AND** the local storage stores `analytics: true`, `personalization: false`, and `advertising: false`

#### Scenario: User reopens cookie settings from Terms page
- **GIVEN** a user who has already closed the cookie banner
- **WHEN** they navigate to `/terminos/` or `/terms/`
- **AND** they click on the "panel de control de cookies" link or button
- **THEN** the Cookie Consent Panel is displayed again with their previously saved preferences pre-selected
- **WHEN** they change a preference and click "Guardar preferencias"
- **THEN** their new preference is saved to local storage
- **AND** the panel is dismissed

### Requirement: Web Interface Accessibility & Usability (Cookie Banner)
The Cookie Consent Banner MUST comply with the Vercel Web Interface Guidelines.
Specifically:
- **Focus States**: All buttons (Aceptar todo, Rechazar todo, Personalizar, Guardar preferencias) and inputs (toggle switches) MUST have visible focus rings using `:focus-visible` when focused.
- **Labels & Hit Targets**: Every toggle switch/checkbox MUST share a single hit target with its label, leaving no dead zones.
- **Screen Readers**: Any toggle or button icon MUST be hidden from screen readers using `aria-hidden="true"`, or have a descriptive label.
- **Motion**: If the browser user agent requests reduced motion (`prefers-reduced-motion: reduce`), the banner's slide-up/fade-in animations MUST be disabled or simplified (instant showing/hiding).
- **Transitions**: Transitions MUST list properties explicitly (e.g. `transition-opacity`, `transition-transform`) rather than using `transition: all`.
- **Typography**: Typography MUST use balanced headings (`text-wrap: balance`) and correct quotes (`“`/`”`) and ellipses (`…`).

#### Scenario: Verify accessibility and motion behaviors for cookie banner
- **GIVEN** a user navigating the site
- **WHEN** the cookie banner is active
- **THEN** all buttons have visible focus rings when focused via keyboard
- **AND** all toggles have clickable labels without dead zones
- **AND** the banner behaves instantly when prefers-reduced-motion is active

## MODIFIED Requirements

### Requirement: Public Privacy Policy Page
The application SHALL provide a public Privacy Policy page accessible at `/privacidad/` and `/privacy/`. This page MUST describe the data collection practices of the service, specifically addressing the sensitive data processed by the app.

The content MUST include:
- **Identity Data**: Use of Google and Microsoft OAuth for authentication and profile retrieval.
- **CV Content**: Storage of PDF documents in secure private buckets and the use of time-limited UUID links for distribution.
- **Payment Data**: Use of Stripe for transaction processing without local storage of credit card numbers.
- **Email Access**: Explicit mention of the `gmail.send` and `Mail.Send` scopes used to send emails on the user's behalf.
- **Google Limited Use Disclosure**: Explicit statement that the use and transfer of information received from Google APIs to any other app will adhere to [Google API Services User Data Policy](https://developers.google.com/terms/api-services-user-data-policy), including the Limited Use requirements.
- **Global Blacklist Disclosure**: Statement explaining that if a recipient unsubscribes, they are added to a global blacklist that prevents all FastJob users from contacting them.
- **Cookies**: Disclosure of functional-only cookies (session and CSRF) required for the operation of the service.
- **Retention**: Data retention policies for account deletion and financial records (tax compliance).

#### Scenario: Anonymous visitor views the Privacy Policy
- **GIVEN** a visitor on the landing page
- **WHEN** they click "Privacidad" in the footer
- **THEN** they navigate to `/privacidad/`
- **AND** the page displays the detailed privacy policy within the global brand layout, including explicit details for both Google's `gmail.send` and Microsoft's `Mail.Send` permissions
