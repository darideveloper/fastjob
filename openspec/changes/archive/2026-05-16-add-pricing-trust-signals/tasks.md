# Tasks: add-pricing-trust-signals

Ordered by dependency; all items are small and independently verifiable.

## Backend

- [x] **T1** — In `apps/payments/views.py::packages()`, import `MailingLog`
      from `apps.mailing.models` and add `successful_sends_count` to the
      render context.
      _Validation_: `assert context["successful_sends_count"] >= 0`

## Template

- [x] **T2** — In `templates/payments/packages.html`, load
      `{% load humanize %}` at the top and render the green badge inside
      each card's price block (`<div class="mb-6">` at line 26).
      Show the badge only when `successful_sends_count > 0`.
      _Validation_: Visual check in dev server at `/payments/paquetes/`.

- [x] **T3** — Add the page-footer trust bar paragraph below the Stripe
      disclaimer (after line 69). Also guard with `{% if successful_sends_count > 0 %}`.
      _Validation_: Visual check with at least one `MailingLog(status='sent')` fixture.

## Tests

- [x] **T4** — In `apps/payments/tests/`, add a test that calls `GET /payments/paquetes/`
      with a logged-in user and asserts `successful_sends_count` is present in
      the template context and equals `MailingLog.objects.filter(status='sent').count()`.

- [x] **T5** — Add a test for the zero-state: no `MailingLog` rows exist →
      the badge HTML (`envíos exitosos en la plataforma`) is absent from
      the rendered page.

## Dependencies
T2 and T3 depend on T1. T4 and T5 depend on T1.
T2 and T3 are independent of each other (parallel).
T4 and T5 are independent of each other (parallel).
