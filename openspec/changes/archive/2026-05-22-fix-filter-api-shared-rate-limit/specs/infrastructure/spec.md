## ADDED Requirements

### Requirement: Trusted Reverse-Proxy Client IP Resolution

Any feature that distinguishes individual visitors by network origin — in particular per-IP rate limiting — MUST resolve the real client IP from the `X-Forwarded-For` request header rather than from `REMOTE_ADDR`, because the application runs behind a reverse proxy (Traefik on Coolify) where `REMOTE_ADDR` is the proxy's address and is identical for every visitor.

Resolution MUST be trust-bounded: the number of reverse-proxy hops the deployment controls MUST be operator-configurable (env var `TRUSTED_PROXY_HOPS`, default `1`), and the resolver MUST select the `X-Forwarded-For` entry contributed by the outermost trusted proxy (the entry at index `-TRUSTED_PROXY_HOPS`, counting from the right). Entries to the left of that position are client-controlled and MUST NOT be trusted. When the header is absent, blank, has fewer entries than `TRUSTED_PROXY_HOPS`, or the selected entry is not a valid IP address, the resolver MUST fall back to `REMOTE_ADDR` and MUST always return a non-empty string. The resolver MUST be wired into `django-ratelimit` via `RATELIMIT_IP_META_KEY` so that every `@ratelimit(key="ip", ...)` limiter in the project keys on the real client IP.

#### Scenario: Single trusted proxy resolves the real client

- **GIVEN** `TRUSTED_PROXY_HOPS = 1`
- **AND** a request arrives via Traefik with `X-Forwarded-For: 203.0.113.7` and `REMOTE_ADDR` set to the Traefik container IP
- **WHEN** the client IP is resolved
- **THEN** the resolved IP is `203.0.113.7`, not the Traefik container IP

#### Scenario: Two visitors behind one proxy get distinct identities

- **GIVEN** `TRUSTED_PROXY_HOPS = 1` and both requests share the same `REMOTE_ADDR` (the proxy)
- **WHEN** visitor A arrives with `X-Forwarded-For: 198.51.100.1` and visitor B with `X-Forwarded-For: 198.51.100.2`
- **THEN** the resolver returns `198.51.100.1` for A and `198.51.100.2` for B
- **AND** any per-IP rate limit counts them in separate buckets

#### Scenario: Spoofed left-hand entries are ignored

- **GIVEN** `TRUSTED_PROXY_HOPS = 1`
- **WHEN** a request arrives with `X-Forwarded-For: 1.1.1.1, 203.0.113.7` (the client pre-seeded `1.1.1.1`)
- **THEN** the resolved IP is `203.0.113.7` (the entry the trusted proxy appended)
- **AND** the client-supplied `1.1.1.1` is not used

#### Scenario: Malformed or missing header falls back safely

- **WHEN** a request has no `X-Forwarded-For` header, or the selected entry is not a valid IP address, or the header has fewer entries than `TRUSTED_PROXY_HOPS`
- **THEN** the resolver returns `REMOTE_ADDR`
- **AND** the resolver never returns an empty string

#### Scenario: Additional trusted hop for a CDN deployment

- **GIVEN** `TRUSTED_PROXY_HOPS = 2` (a CDN sits in front of Traefik)
- **WHEN** a request arrives with `X-Forwarded-For: 203.0.113.7, 70.0.0.9` (client, then CDN edge as seen by Traefik)
- **THEN** the resolved IP is `203.0.113.7` (the entry at index `-2`)
