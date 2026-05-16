## ADDED Requirements

### Requirement: Custom 404 handler with XHR/HTML split
The application SHALL provide a custom `handler404` registered via `config/urls.py` that returns a structured JSON error body for XHR/AJAX clients and renders the `templates/404.html` template for browser clients, mirroring the behavior of the existing `handler400`.

#### Scenario: XHR client hits a nonexistent URL
- **WHEN** a request with `X-Requested-With: XMLHttpRequest` or `Accept: application/json` is sent to any URL that does not match a registered route
- **THEN** the server MUST respond with HTTP 404
- **AND** the `Content-Type` header MUST be `application/json`
- **AND** the response body MUST be a JSON object containing an `"error"` key with a human-readable Spanish message

#### Scenario: Browser client hits a nonexistent URL
- **WHEN** a standard browser request (no XHR detection headers) is sent to a nonexistent URL
- **THEN** the server MUST respond with HTTP 404
- **AND** the response MUST render the `404.html` template
- **AND** the `Content-Type` MUST be `text/html`

#### Scenario: 404 handler falls back gracefully when template is missing
- **WHEN** the `404.html` template does not exist on disk
- **THEN** the handler MUST NOT raise an unhandled exception
- **AND** MUST respond with a plain `text/html` fallback body containing "404"

### Requirement: Custom 500 handler with XHR/HTML split
The application SHALL provide a custom `handler500` registered via `config/urls.py` that returns a structured JSON error body for XHR/AJAX clients and renders the `templates/500.html` template for browser clients.

Django's `handler500` contract differs from 400/404: the view signature is `handler500(request)` with no `exception` argument (Django has already logged the traceback at this point). The handler MUST NOT attempt to read or log the exception itself.

#### Scenario: XHR client triggers a server error
- **WHEN** a request with `X-Requested-With: XMLHttpRequest` or `Accept: application/json` results in an unhandled server exception
- **THEN** the server MUST respond with HTTP 500
- **AND** the `Content-Type` header MUST be `application/json`
- **AND** the response body MUST be a JSON object containing an `"error"` key

#### Scenario: Browser client triggers a server error
- **WHEN** a standard browser request results in an unhandled server exception
- **THEN** the server MUST respond with HTTP 500
- **AND** the response MUST render the `500.html` template
- **AND** the `Content-Type` MUST be `text/html`

#### Scenario: 500 handler falls back gracefully when template is missing
- **WHEN** the `500.html` template does not exist on disk
- **THEN** the handler MUST NOT raise a secondary exception
- **AND** MUST respond with a plain `text/html` fallback body containing "500"

### Requirement: Error handlers share XHR detection logic
All custom error handlers (400, 404, 500) in `config/error_handlers.py` SHALL use the same `_is_xhr(request)` helper to determine whether the client expects JSON or HTML, ensuring consistent XHR detection across all error states without duplication.

#### Scenario: XHR detection is centralized
- **WHEN** a request is classified as XHR by `_is_xhr`
- **THEN** ALL three handlers (400, 404, 500) MUST produce a `Content-Type: application/json` response
- **AND** the detection logic (checking `X-Requested-With` and `Accept` headers) MUST appear only in `_is_xhr`, not repeated in each handler
