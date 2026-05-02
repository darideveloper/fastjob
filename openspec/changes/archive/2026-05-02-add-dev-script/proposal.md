# Change: Add Dev Script

## Why
Currently, starting the application locally requires opening four terminal windows (Django server, Celery worker, Celery beat, and Stripe CLI) and manually starting a localtunnel for OAuth redirects. This is tedious and error-prone.

## What Changes
- Create a `dev.sh` script using `tmux` to start all required services (Django, Celery Worker, Celery Beat, Stripe CLI, and Localtunnel) concurrently.
- Implement dynamic port detection in `dev.sh` starting from port 8000 to avoid conflicts with other local projects.
- Update `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` in `.env.example` and `config/settings.py` to include `fastjob.loca.lt`.
- Configure the application to use `fastjob.loca.lt` as the primary local development domain (without ports) to streamline OAuth and webhooks.
- Update project documentation to instruct developers to use `dev.sh`.

## Impact
- Affected specs: `dev-environment`
- Affected code: `config/settings.py`, `.env.example`, `dev.sh`, `README.md`
