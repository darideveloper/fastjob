# infrastructure Specification

## Purpose
Define the requirements for deploying the FastJob application to various environments (Production, Staging, PaaS). It ensures consistency in proxying, security headers, and service orchestration.

## ADDED Requirements

### Requirement: Coolify One-Click Compatibility
The infrastructure configuration MUST support automated deployment on Coolify with zero manual file editing.

#### Scenario: A user imports the repository into Coolify.
- **Given** the user has a Coolify instance
- **When** they import the FastJob repository
- **Then** Coolify MUST automatically identify the `docker-compose.yml`
- **AND** the configuration MUST use `SERVICE_URL_*` variables for proxying.
- **AND** all database/redis connections MUST use internal service discovery.

### Requirement: Health-Aware Orchestration
Services MUST wait for their dependencies to be fully ready (healthy) before starting.

#### Scenario: The stack is started via Docker Compose.
- **When** `docker compose up` is executed
- **Then** the `db` and `redis` services MUST perform healthchecks.
- **AND** the `web` and `celery` services MUST NOT start until `db` and `redis` report a `healthy` status.

### Requirement: Dynamic Host Security
Application security headers (ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS) MUST dynamically adapt to the deployment URL.

#### Scenario: The application is deployed to a dynamic Coolify subdomain.
- **Given** Coolify assigns `https://fastjob-xyz.coolify.io` to the `web` service
- **When** the application starts
- **Then** `ALLOWED_HOSTS` MUST include `fastjob-xyz.coolify.io`.
- **AND** `CSRF_TRUSTED_ORIGINS` MUST include `https://fastjob-xyz.coolify.io`.
