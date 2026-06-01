# Design: Legal Pages Architecture and Content

## 1. Overview
The legal pages (Privacy Policy and Terms of Service) are public-facing static pages that define the contractual and data-handling relationship between FastJob and its users.

## 2. Technical Implementation
### 2.1 Views and URLs
To minimize overhead, we will use Django's built-in `TemplateView`.
- **URL Schema**:
  - `GET /privacidad/` -> `PrivacyView` (`templates/legal/privacy.html`)
  - `GET /terminos/` -> `TermsView` (`templates/legal/terms.html`)

### 2.2 Template Inheritance
The new templates will extend `base.html` to maintain the brand identity (colors, navbar, footer) and responsive behavior.

## 3. Content Strategy
The content will be structured to address the specific "Restricted Scopes" and "Sensitive Data" handled by the app.

### 3.1 Privacy Policy Content
- **Information Collection**:
    - Identity (OAuth Google/Microsoft).
    - CV Content (PDFs stored in DigitalOcean).
    - Payment IDs (Stripe).
- **Processing Purposes**:
    - Delegated email sending.
    - Temporary CV hosting (UUID-based).
- **Third-Party Disclosures**: Stripe, DigitalOcean, Google, Microsoft.
- **Security Measures**: Link expiration (5 min), UUID entropy, rate limiting.

### 3.2 Terms of Service Content
- **Service Nature**: Automation tool, not a recruitment agency.
- **Usage Rules**: Prohibition of spam, illegal content, or reverse-engineering.
- **Credits (Envíos)**: Consumable units, non-refundable once used.
- **Liability**: No guarantee of employment results; no liability for third-party provider (Google/Microsoft) account actions.

## 4. Alternative Considered: Database-backed Content
- **Pros**: Dynamic editing via Django Admin.
- **Cons**: Requires new models, migrations, and complex HTML sanitization (if using RichText).
- **Decision**: Rejected. For a lean MVP, static templates are easier to version control and review.
