# legal Specification (Delta)

## ADDED Requirements

### Requirement: Public Privacy Policy Page
The application SHALL provide a public Privacy Policy page accessible at `/privacidad/`. This page MUST describe the data collection practices of the service, specifically addressing the sensitive data processed by the app.

The content MUST include:
- **Identity Data**: Use of Google and Microsoft OAuth for authentication and profile retrieval.
- **CV Content**: Storage of PDF documents in secure private buckets and the use of time-limited UUID links for distribution.
- **Payment Data**: Use of Stripe for transaction processing without local storage of credit card numbers.
- **Email Access**: Explicit mention of the `gmail.modify` and `Mail.Send` scopes used to send emails on the user's behalf.
- **Google Limited Use Disclosure**: Explicit statement that the use and transfer of information received from Google APIs to any other app will adhere to [Google API Services User Data Policy](https://developers.google.com/terms/api-services-user-data-policy), including the Limited Use requirements.
- **Global Blacklist Disclosure**: Statement explaining that if a recipient unsubscribes, they are added to a global blacklist that prevents all FastJob users from contacting them.
- **Cookies**: Disclosure of functional-only cookies (session and CSRF) required for the operation of the service.
- **Retention**: Data retention policies for account deletion and financial records (tax compliance).

#### Scenario: Anonymous visitor views the Privacy Policy
- **GIVEN** a visitor on the landing page
- **WHEN** they click "Privacidad" in the footer
- **THEN** they navigate to `/privacidad/`
- **AND** the page displays the detailed privacy policy within the global brand layout

### Requirement: Public Terms of Service Page
The application SHALL provide a public Terms of Service page accessible at `/terminos/`. This page MUST define the legal agreement between the user and the service.

The content MUST include:
- **Service Definition**: FastJob is an automation tool, not a recruitment agency or employer.
- **Credits (Envíos)**: Definition of "Envíos" as consumable units that expire upon use and are non-refundable.
- **Acceptable Use**: Prohibition of using the service for spam, malware distribution, or illegal activities.
- **Liability Disclaimer**: Disclaimer of liability regarding job placement results and actions taken by third-party email providers (Google/Microsoft).

#### Scenario: User views the Terms of Service
- **GIVEN** any user (anonymous or authenticated)
- **WHEN** they navigate to `/terminos/`
- **THEN** the page displays the terms of service covering service rules and liability.
