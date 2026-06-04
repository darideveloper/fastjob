## Context

Currently, the `fastjob` application records Stripe credit purchases in the `StripePayment` model, which maps to users and packages. While administrators can see these payments through the Django admin interface, users have no visibility into their purchase histories or access to download past receipts.

## Goals / Non-Goals

**Goals:**
- Retrieve and display the payment history for the logged-in user in their dashboard view.
- Render the transaction list with concept, date/time, credits, amount, and payment status badges.
- Provide a link to the user's hosted Stripe Billing Portal for downloading invoices/receipts.
- Gracefully handle empty states for users with no payment history.
- Ensure the unit test suite runs and passes cleanly by fixing a test URL reversal issue.

**Non-Goals:**
- Creating a separate page layout for payments (Option A was selected).
- Refactoring the Stripe webhook or checkout flows.
- Providing pdf/invoice downloads directly from the Django backend (relying on Stripe Billing Portal instead).

## Decisions

### 1. Unified Dashboard Section vs. Dedicated Page
- **Decision:** Unified Dashboard Section (Option A).
- **Rationale:** Keeps the user experience simple. Users can see how many credits they purchased, their remaining credits, and their transaction logs in one place without jumping to another page.
- **Alternatives considered:** A dedicated payments page. It was rejected to avoid adding unnecessary pages and complexity to the client app menu structure at this stage.

### 2. Django View Query Optimization
- **Decision:** Query payments with `select_related('package')` and order by `-created_at`.
- **Rationale:** Using `select_related('package')` avoids the N+1 query problem, as package information (like the package name) is rendered in the payment table. Ordering by `-created_at` ensures the newest payments are always visible first.

### 3. Stripe Billing Portal Integration
- **Decision:** Link directly to the existing `billing_portal` view from the history header.
- **Rationale:** Uses Stripe's secure, hosted environment for downloading invoices, eliminating the need to store or serve PDF files from the local Django media storage.

### 4. Fix Pre-existing test_error_handlers.py failure
- **Decision:** Declare dummy URLs for `privacy` and `terms` in the test URLconf.
- **Rationale:** The error handler tests override the main `ROOT_URLCONF` with a mock module. Since `base.html` includes footer links that reverse `privacy` and `terms`, rendering any error pages inside the tests was raising a `NoReverseMatch` error. Declaring dummy routes satisfies Django's URL resolver.

## Risks / Trade-offs

- **Risk:** Cluttering the main dashboard page on viewports with small heights if the user has many payments.
  - **Mitigation:** The payments table is appended at the bottom, so it does not interfere with the primary CTA controls or recent activity. A scroll container (`overflow-x-auto`) is used to prevent layout breakages on mobile screens.
