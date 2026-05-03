# Proposal: Configure Coolify One-Click Deployment

## Summary
Transform the existing `docker-compose.yml` into a "Coolify-ready" configuration that enables one-click deployment. This includes utilizing Coolify's automated proxying (via `SERVICE_FQDN_*` variables), dynamic environment variable injection, and production-optimized container settings.

## Why
The current `docker-compose.yml` is mixed with development concerns (local volumes, fixed port mappings) and lacks the specific metadata/variables required for Coolify to automatically handle SSL, proxying, and service discovery. Deploying to Coolify currently requires manual intervention to map environment variables and setup the proxy.

## Proposed Changes
1.  **Refactor `docker-compose.yml`**:
    *   Add **Coolify Metadata Headers** (slogan, category, port) for catalog integration.
    *   Introduce `SERVICE_URL_*` variables for `web` and `flower` services to handle `https://` protocol automatically.
    *   Explicitly map environment variables in the `environment` block, using `${VAR:?}` for mandatory secrets.
    *   Utilize Coolify's auto-generated database credentials (`SERVICE_USER_POSTGRES`, etc.).
    *   Remove development-only volume mounts (`- .:/app`).
    *   Implement `${COOLIFY_VOLUME_*}` placeholders for persistent data.
    *   Add robust healthchecks for `db` and `redis`.
    *   Configure `depends_on` with healthcheck conditions to ensure proper startup sequence.
2.  **Infrastructure Specification**:
    *   Define a new `infrastructure` capability to document deployment requirements and standards.
3.  **Deployment Documentation**:
    *   Update `docs/deploy.md` to include Coolify-specific instructions.

## Expected Impact
*   **One-Click Deployment**: Users can import the repository into Coolify and have it running with minimal configuration.
*   **Automated SSL/Proxy**: SSL certificates and reverse proxying will be handled automatically by Coolify's Traefik/Caddy instance.
*   **Improved Reliability**: Healthcheck-aware container orchestration prevents the web application from starting before the database is ready.
