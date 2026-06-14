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
- **Cookies**: Disclosure of cookies required for the operation of the service.
- **Retention**: Data retention policies for account deletion and financial records (tax compliance).
- **Language and Disclosures**: 
  - The Spanish URL `/privacidad/` MUST serve the content in Spanish.
  - The English URL `/privacy/` MUST serve the content in English.
  - The English version MUST include a highly visible, explicit Google and Microsoft API Data Sharing and Transfer Disclosure stating that the application does not share, sell, rent, trade, transfer, or disclose Google/Microsoft user data to third parties under any circumstances.

#### Scenario: Anonymous visitor views the Privacy Policy in Spanish
- **GIVEN** a visitor on the landing page
- **WHEN** they click "Privacidad" in the footer
- **THEN** they navigate to `/privacidad/`
- **AND** the page displays the detailed privacy policy in Spanish within the global brand layout

#### Scenario: User views the Privacy Policy in English
- **WHEN** they navigate to `/privacy/`
- **THEN** the page displays the detailed privacy policy in English within the global brand layout, including explicit data sharing and transfer disclosures for Google and Microsoft API scopes

### Requirement: Public Terms of Service Page
The application SHALL provide a public Terms of Service page accessible at both `/terminos/` and `/terms/`. This page MUST define the legal agreement between the user and the service.

The content MUST include:
- **Aviso Legal (General Info)**: Fernando Peña Torre identity, CIF, registration, address, and the domain `www.fastjob.es`. Condition of access, and definition of "Usuario". It MUST include the warning:
  > *"En caso de que no acepte los términos y condiciones que a continuación se presentan le rogamos se abstenga de utilizar el Sitio Web, reservándose la Sociedad el derecho a restringir el acceso al Sitio Web a aquellos usuarios que no los respeten."* (Or the corresponding English translation for the English page).
- **Platform Definition**: FastJob is an automation tool, not a recruiter/employer, and guarantees no job interviews/offers.
- **Envíos Credits**: Definition of "Envíos" as consumable units that expire upon use and are non-refundable.
- **Third-Party Providers**: Delegated OAuth permissions and disclaimer of liability for account suspensions by Google/Microsoft.
- **Unsecured Channel Warning & Data Protection**: Disclaimer that communication channels are not encrypted, warning against sending sensitive/protected data.
- **Cookie Policy**: Details classifications and browser removal links with explicit anchor texts matching the target document.
- **Social Media (Instagram)**: Instagram page information and data controller details.
- **Linking Policy**: External links liability disclaimer.
- **Applicable Spanish Legislation**: LSSI-CE 34/2002 and LOPDGDD 3/2018.
- **Contacto y Soporte**: Link to `www.basquekide.es` and `dpo@basquekide.es` at the bottom of the page.
- **Language Support**:
  - The Spanish URL `/terminos/` MUST serve the content in Spanish.
  - The English URL `/terms/` MUST serve the content in English.

#### Scenario: User views the Terms of Service via Spanish URL
- **WHEN** they navigate to `/terminos/`
- **THEN** the page displays the terms of service in Spanish covering service rules, cookie policy, social media privacy, and liability.

#### Scenario: User views the Terms of Service via English URL
- **WHEN** they navigate to `/terms/`
- **THEN** the page displays the terms of service in English covering service rules, cookie policy, social media privacy, and liability.
