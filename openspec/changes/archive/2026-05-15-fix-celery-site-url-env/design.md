## Context
The application relies on `SITE_DOMAIN` and `SITE_SCHEME` to construct absolute URLs for emails and other external-facing links. These are defined in `config/settings.py` using `decouple.config`.

## Goals
- Ensure all services that run Django code (web, worker, beat) have access to the correct site identity environment variables.

## Decisions
- **Inject variables directly in `docker-compose.yml`**: Since `web` already has them, we will replicate the same logic for `celery_worker` and `celery_beat`.

## Risks / Trade-offs
- None identified. This is a straightforward configuration fix.
