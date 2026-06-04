# payment-history Specification

## Purpose
Track, display, and manage the user's Stripe credit purchases and provide access to the Stripe Customer Portal for downloading invoices.

## Requirements
### Requirement: Payment History Section in Dashboard
The dashboard SHALL display a section showing the logged-in user's payment history, including concept, credits granted, amount paid, transaction date/time, and transaction status.

#### Scenario: User has payments
- **WHEN** a user visits the dashboard and has one or more recorded payments
- **THEN** the dashboard renders a table listing those payments with Concept, Envíos, Importe, Fecha, and Estado.

#### Scenario: User has no payments
- **WHEN** a user visits the dashboard and has no recorded payments
- **THEN** the dashboard renders a friendly empty state message with a link to view available packages.

### Requirement: Stripe Billing Portal Integration
The payment history section SHALL contain a button that redirects users to Stripe's hosted Billing Portal to download invoices and receipts.

#### Scenario: Redirection to Billing Portal
- **WHEN** a user clicks the "Facturación y Recibos (Stripe)" button on the payment history section
- **THEN** the system redirects them to the Stripe billing portal.

### Requirement: Payment Status Badges
The payment history table SHALL display visual status badges with appropriate semantic colors indicating the status of each payment.

#### Scenario: Status badge styling
- **WHEN** the user views a completed transaction
- **THEN** the status badge displays "Completado" with green styling.
- **WHEN** the user views a pending transaction
- **THEN** the status badge displays "Pendiente" with amber styling.
- **WHEN** the user views a failed transaction
- **THEN** the status badge displays "Fallido" with red styling.
