# infrastructure Specification

## Purpose
Add requirements for accurate, per-service container healthchecks so orchestrators, Coolify, and Netdata report real liveness for every service, including non-HTTP ones.

## ADDED Requirements

### Requirement: Accurate Healthchecks for Non-HTTP Services
The `celery_worker`, `celery_beat`, and `flower` services MUST define their own compose healthchecks that reflect their actual runtime state, and MUST NOT rely on any image-level healthcheck that assumes an HTTP listener on port 8000.

#### Scenario: Services that do not serve HTTP remain healthy
- **Given** `celery_worker`, `celery_beat`, or `flower` is running and functioning
- **When** Docker runs its healthcheck
- **Then** the check MUST pass while the service is functioning
- **AND** the check MUST NOT depend on `localhost:8000` being reachable

#### Scenario: Worker health requires a broker control reply
- **Given** the `celery_worker` service is running
- **When** its healthcheck runs
- **Then** the check MUST verify the worker replies to a Celery control ping scoped to the container's own hostname
- **AND** the check MUST target the broker the worker is configured to use

#### Scenario: Flower health requires an authenticated dashboard response
- **Given** the `flower` container is running with `FLOWER_BASIC_AUTH` set
- **When** its healthcheck runs
- **Then** the check MUST verify the dashboard responds over HTTP with valid `FLOWER_BASIC_AUTH` credentials
- **AND** the credential MUST be available as a container environment variable at runtime

### Requirement: No False-Unhealthy From Inherited Checks
The application image MUST NOT ship a global `HEALTHCHECK` that a non-web service can silently inherit and fail.

#### Scenario: A service omits its own healthcheck
- **Given** a service is built from the application image and does not define its own compose healthcheck
- **When** the container starts
- **Then** Docker MUST report no health status rather than "unhealthy"

### Requirement: Orchestrator Health Status Reflects Real Liveness
The health status reported to orchestrators and monitoring (Coolify dashboard, Netdata `docker_container_unhealthy` alerts) MUST reflect each service's actual runtime state, so a running service is never reported "unhealthy" due to a healthcheck that assumes the web role.

#### Scenario: Coolify and Netdata report running services as healthy
- **Given** `celery_worker`, `celery_beat`, and `flower` are running and functioning
- **When** Coolify and Netdata query their Docker health status
- **Then** the services MUST be reported as `healthy`
- **AND** Netdata MUST NOT raise `docker_container_unhealthy` for them