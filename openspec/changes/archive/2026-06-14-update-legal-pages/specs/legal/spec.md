## MODIFIED Requirements

### Requirement: Public Privacy Policy Page
The application SHALL provide a public Privacy Policy page accessible at both `/privacidad/` and `/privacy/`. This page MUST describe the data collection practices of the service, specifically addressing the sensitive data processed by the app.

The content MUST include:
- **Identidad del Responsable**: Fernando Peña Torre, CIF 79050303Q, Address: C\ Almagro 11 - 28010 Madrid.
- **Capa Informativa (Contratación)**: Purpose (manage contracted service), legal basis (contract performance), no sharing except legal obligation, and GDPR rights (access, rectification, erasure, limitation, opposition, portability).
- **Capa Informativa (Contacto)**: Purpose (manage contact/support request), legal basis (consent), and the option to withdraw consent at any time without retroactive effects.
- **Additional Clauses**: Reference to consulting detailed info at physical head office, assumption of data accuracy unless notified, and immediate deletion of non-consented data.
- **Google API Limited Use & Sharing Disclosures**: Explicit mention of the `gmail.send` scope, Google API limited use statement, and an explicit disclosure stating that **no Google user data is shared, sold, transferred, or disclosed** to third parties.
- **Almacenamiento de CV**: Private DigitalOcean Spaces buckets with temporary (5-minute expiration) UUID download links.
- **Global Blacklist**: Platform-level opt-out for unsubscribed emails.
- **GDPR Rights Contact**: **dpo@basquekide.es** for exercising rights.
- **Contacto y Soporte**: Link to `www.basquekide.es` and `dpo@basquekide.es` at the bottom of the page.

#### Scenario: Anonymous visitor views the Privacy Policy via Spanish URL
- **WHEN** they click "Privacidad" in the footer
- **THEN** they navigate to `/privacidad/`
- **AND** the page displays the detailed privacy policy within the global brand layout

#### Scenario: Google reviewer views the Privacy Policy via English URL
- **WHEN** they navigate to `/privacy/`
- **THEN** they see the same Privacy Policy page containing the Google data sharing disclosures

### Requirement: Public Terms of Service Page
The application SHALL provide a public Terms of Service page accessible at both `/terminos/` and `/terms/`. This page MUST define the legal agreement between the user and the service.

The content MUST include:
- **Aviso Legal (General Info)**: Fernando Peña Torre identity, CIF, registration, address, and the domain `www.fastjob.es`. Condition of access, and definition of "Usuario".
- **Platform Definition**: FastJob is an automation tool, not a recruiter/employer, and guarantees no job interviews/offers.
- **Envíos Credits**: Definition of "Envíos" as consumable units that expire upon use and are non-refundable.
- **Third-Party Providers**: Delegated OAuth permissions and disclaimer of liability for account suspensions by Google/Microsoft.
- **Unsecured Channel Warning**: Disclaimer that communication channels are not encrypted, warning against sending sensitive/protected data.
- **Cookie Policy**: Detailed classifications (source, purpose, persistence), browser removal links, and Cookie banner requirements (technical-only by default, 90-day reset).
- **Social Media (Instagram)**: Instagram privacy policy link and user responsibility for Instagram content.
- **Linking Policy**: External links liability disclaimer.
- **Applicable Spanish Legislation**: LSSI-CE 34/2002 and LOPDGDD 3/2018.
- **Contacto y Soporte**: Link to `www.basquekide.es` and `dpo@basquekide.es` at the bottom of the page.

#### Scenario: User views the Terms of Service via Spanish URL
- **WHEN** they navigate to `/terminos/`
- **THEN** the page displays the terms of service covering service rules, cookie policy, social media privacy, and liability.

#### Scenario: User views the Terms of Service via English URL
- **WHEN** they navigate to `/terms/`
- **THEN** the page displays the same terms of service covering service rules, cookie policy, social media privacy, and liability.
