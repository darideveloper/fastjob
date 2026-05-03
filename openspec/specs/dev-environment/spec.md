# dev-environment Specification

## Purpose
TBD - created by archiving change add-dev-script. Update Purpose after archive.
## Requirements
### Requirement: Development Environment Domain Support
The application MUST support incoming requests from the development localtunnel subdomain (`fastjob.loca.lt`) and correctly handle HTTPS termination.

#### Scenario: A developer initiates Microsoft OAuth login via localtunnel.
- **Given** the application is running via `localtunnel` at `https://fastjob.loca.lt`
- **AND** `TRUST_PROXY_SSL_HEADER` is set to `True`
- **When** the developer clicks "Login with Microsoft"
- **Then** the generated `redirect_uri` sent to Microsoft MUST use the `https` scheme.
- **AND** the URI MUST be `https://fastjob.loca.lt/accounts/microsoft/login/callback/`.

### Requirement: Unified Local Development Script
The project MUST provide a unified script (`dev.sh`) to start all local development processes.

#### Scenario: A developer wants to start the development environment with one command.
- **Given** the developer has `tmux` installed
- **When** they execute `./dev.sh`
- **Then** a `tmux` session is created with dedicated windows running the Django server, Celery worker, Celery beat, Stripe CLI, and Localtunnel for the `fastjob` subdomain.

#### Scenario: A developer starts the environment when port 8000 is already in use.
- **Given** port 8000 is occupied by another process
- **When** the developer executes `./dev.sh`
- **Then** the script automatically identifies the next available port (e.g., 8001)
- **AND** the Django server and Localtunnel are configured to use that specific available port.

