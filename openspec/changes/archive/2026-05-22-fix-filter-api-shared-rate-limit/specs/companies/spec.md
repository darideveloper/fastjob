## MODIFIED Requirements

### Requirement: Public Filter-Options Endpoint

The system SHALL expose a read-only HTTP endpoint at `GET /api/companies/filter-options/` that returns the distinct, non-empty values currently present in `Company.area` and `Company.location`. The endpoint MUST be reachable without authentication and MUST be rate-limited per **real client IP** — the visitor IP resolved per the `infrastructure` capability's `Trusted Reverse-Proxy Client IP Resolution` requirement, NOT the connecting socket address (which behind a reverse proxy is identical for every visitor). The response payload MUST contain only label strings — never any company-identifying field (email, name, primary key, or any other column). All returned values MUST be in lowercase. The response MUST be client-cacheable via a `Cache-Control` header so that browsers and shared caches do not re-fetch the (slow-changing) taxonomy on every page view.

#### Scenario: Anonymous client retrieves option list

- **WHEN** an unauthenticated client sends `GET /api/companies/filter-options/`
- **THEN** the response is `200 OK` with a JSON body `{"areas": [<sorted unique non-empty area strings>], "locations": [<sorted unique non-empty location strings>]}`
- **AND** the response body contains no field other than `areas` and `locations`

#### Scenario: Empty / whitespace values are excluded from the option list

- **GIVEN** a `Company` row with `area = ""` and another with `area = "   "`
- **WHEN** the endpoint is called
- **THEN** neither blank value appears in `areas`

#### Scenario: Values are always returned in lowercase

- **GIVEN** companies linked to areas stored as `"tecnología"` and `"diseño"`
- **WHEN** the endpoint is called
- **THEN** `areas` contains `["diseño", "tecnología"]`
- **AND** all entries are lowercase.

#### Scenario: Per-IP rate limit blocks abuse and is keyed on the resolved client IP

- **WHEN** a single real client IP sends more than the configured per-hour threshold
- **THEN** subsequent requests from that IP within that window receive `429 Too Many Requests`
- **AND** two distinct visitors behind the same reverse proxy are counted in separate buckets, so one visitor exhausting the limit does NOT cause `429` for the other

#### Scenario: Response is client-cacheable

- **WHEN** an unauthenticated client sends `GET /api/companies/filter-options/`
- **THEN** the `200 OK` response includes a `Cache-Control` header permitting shared caching for a bounded period
- **AND** a browser or edge cache may serve a repeat request within that period without contacting the origin

### Requirement: Public Company-Count Endpoint

The system SHALL expose a read-only HTTP endpoint at `GET /api/companies/count/` that accepts optional `area` and `location` query parameters and returns the integer number of companies matching those filters. The endpoint MUST be reachable without authentication, MUST be rate-limited per **real client IP** (resolved per the `infrastructure` capability's `Trusted Reverse-Proxy Client IP Resolution` requirement, NOT the connecting socket address), and MUST return only an integer count — never any company name, email, primary key, or any other row-level data. Filter values MUST be validated against the current allowed-options whitelist; any value outside the whitelist MUST cause the request to be rejected with `400 Bad Request`. A successful response MUST be client-cacheable via a `Cache-Control` header; the `400` validation-failure response MUST NOT be cached.

#### Scenario: Count with no filters returns total eligible companies

- **WHEN** an unauthenticated client sends `GET /api/companies/count/`
- **THEN** the response is `200 OK` with body `{"count": <total non-blacklisted, not-recently-contacted company count>}`

#### Scenario: Count with valid filters uses exact-match semantics

- **GIVEN** companies with `area = "Tecnología"` and `area = "Tecnología Industrial"`
- **WHEN** the client sends `GET /api/companies/count/?area=Tecnología`
- **THEN** the count includes the first row but NOT the second

#### Scenario: Filter value not in whitelist is rejected

- **GIVEN** the current options list does NOT contain the area `"Bricolaje"`
- **WHEN** the client sends `GET /api/companies/count/?area=Bricolaje`
- **THEN** the response is `400 Bad Request` with body `{"error": "invalid_filter"}`
- **AND** the `400` response is not stored by browser or shared caches

#### Scenario: Empty parameter means "no filter on that field"

- **WHEN** the client sends `GET /api/companies/count/?area=&location=Madrid`
- **THEN** the count includes all companies with `location` equal to `"Madrid"` regardless of `area`

#### Scenario: Response payload exposes no company-identifying data

- **WHEN** the endpoint is called with any combination of parameters
- **THEN** the JSON response body's keys are exactly `{"count"}` on success or `{"error"}` on validation failure
- **AND** no key referencing a company's email, name, ID, or other row-level field appears

#### Scenario: Per-IP rate limit blocks abuse and is keyed on the resolved client IP

- **WHEN** a single real client IP sends more than the configured per-hour threshold
- **THEN** subsequent requests from that IP within that window receive `429 Too Many Requests`
- **AND** two distinct visitors behind the same reverse proxy are counted in separate buckets

## ADDED Requirements

### Requirement: Filter API Throttle Configuration and Resilience

The per-IP rate-limit thresholds for `GET /api/companies/filter-options/` and `GET /api/companies/count/` MUST be operator-configurable via environment variables, with defaults high enough that normal human browsing — including multiple users sharing one public IP (corporate or carrier NAT) — is never throttled, while a single client issuing automated, high-volume requests is still blocked.

Because these endpoints are read-only and expose only label strings and integer counts, rate limiting here is abuse-prevention, not a security boundary. A transient failure of the rate-limiter's cache backend MUST NOT cause the endpoints to reject legitimate traffic: the limiter MUST fail open (serve the request) rather than fail closed (block all clients) when it cannot read its counter.

#### Scenario: Thresholds are operator-configurable

- **GIVEN** an operator sets the filter-options and count rate-limit environment variables
- **WHEN** the application starts
- **THEN** the two endpoints enforce the operator-supplied thresholds
- **AND** when the variables are unset, safe high defaults apply and deployment succeeds unchanged

#### Scenario: Cache-backend failure does not throttle everyone

- **GIVEN** the rate-limiter's cache backend cannot return a counter value for a request (e.g. a transient cache outage or counter-key eviction)
- **WHEN** an unauthenticated client calls `GET /api/companies/filter-options/` or `GET /api/companies/count/`
- **THEN** the request is served normally (the limiter fails open)
- **AND** no client receives a `429` solely because the cache backend was unavailable

#### Scenario: A single abusive IP is still throttled

- **GIVEN** the configured thresholds and a healthy cache backend
- **WHEN** one real client IP exceeds its configured per-hour threshold
- **THEN** further requests from that IP within the window receive `429 Too Many Requests`
