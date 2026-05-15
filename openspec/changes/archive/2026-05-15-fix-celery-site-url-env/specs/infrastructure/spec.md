## ADDED Requirements

### Requirement: Consistent Site Identity for Django Services
All services running the Django application (including `web`, `celery_worker`, and `celery_beat`) MUST have access to the `SITE_DOMAIN`, `SITE_SCHEME`, and `SITE_NAME` environment variables to ensure consistent generation of absolute URLs (e.g., in emails, notifications, and Stripe links).

#### Scenario: Celery worker generates an unsubscribe link
- **Given** the application is deployed with `SITE_DOMAIN=fastjob.es` and `SITE_SCHEME=https`
- **When** the `celery_worker` service processes the `process_mailing_queue` task
- **Then** the generated unsubscribe links MUST start with `https://fastjob.es/`
- **AND** they MUST NOT fall back to `https://localhost/`.

#### Scenario: Celery beat schedules a task
- **Given** the application is deployed with `SITE_DOMAIN=fastjob.es` and `SITE_SCHEME=https`
- **When** the `celery_beat` service initializes or schedules a task that requires URL generation
- **Then** it MUST have access to the correct site identity variables.
