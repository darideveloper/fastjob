# Design: Coolify Integration for FastJob

## Overview
Coolify is a self-hosted PaaS that automates deployment workflows. It relies on specific environment variable patterns and Docker Compose labels to orchestrate services.

## Mapping Strategy

### 1. Metadata Header (One-Click Template)
The `docker-compose.yml` will include a metadata block as comments to populate the Coolify service catalog:
- `documentation`: Link to the project's deployment docs.
- `slogan`: "Self-hosted job application automation."
- `port`: `8000` (Main web entry point).

### 2. Reverse Proxying & SSL
Coolify uses the `SERVICE_URL_<SERVICE_NAME>_<PORT>` pattern to provide the full protocol and domain.
- **Web**: `SERVICE_URL_WEB_8000` (Used for `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`).
- **Flower**: `SERVICE_URL_FLOWER_5555` (Used for task monitoring access).

### 3. Service Discovery & Internal Networking
Instead of using fixed hostnames or IP addresses, we will use the service names defined in `docker-compose.yml` (`db`, `redis`).
- `DATABASE_URL`: `postgres://${SERVICE_USER_POSTGRES}:${SERVICE_PASSWORD_POSTGRES}@db:5432/fastjob`
- `REDIS_URL`: `redis://redis:6379/0`
- `CACHE_REDIS_URL`: `redis://redis:6379/1`

### 4. Environment Variable Injection & Validation
- **Required Secrets**: Use `${SECRET_KEY:?}` and other mandatory keys to ensure Coolify prompts the user before deployment.
- **Auto-Generated Secrets**: Use `SERVICE_PASSWORD_POSTGRES` for the database.
- **Escaping**: Use `$$` for variables like `$$SERVICE_URL_WEB_8000` when used inside other strings (e.g., in `CSRF_TRUSTED_ORIGINS`) to ensure correct runtime evaluation.

### 5. Container Lifecycle & Healthchecks
- **PostgreSQL**: Use `pg_isready` for healthchecks.
- **Redis**: Use `redis-cli ping`.
- **Web**: Use the existing `/healthz` endpoint.
- **Dependencies**: Use `depends_on` with `service_healthy` condition.

## Volume Persistence
To follow Coolify's template standards, we will use the volume placeholder pattern:
- `db`: `${COOLIFY_VOLUME_POSTGRES_DATA:-postgres_data}:/var/lib/postgresql/data`

## Security
- `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` will dynamically include the Coolify URL.
- `SECURE_PROXY_SSL_HEADER` will be enabled via `TRUST_PROXY_SSL_HEADER=True`.
