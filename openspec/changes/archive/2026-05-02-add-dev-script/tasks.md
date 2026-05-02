## 1. Configuration
- [x] 1.1 Update `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` in `config/settings.py` defaults to include `fastjob.loca.lt`.
- [x] 1.2 Update `.env.example` with the new allowed host and trusted origin.

## 2. Dev Script
- [x] 2.1 Create `dev.sh` script that uses `tmux` to spawn windows for Django, Celery Worker, Celery Beat, Stripe CLI, and Localtunnel. The script MUST dynamically find the first available port starting from 8000 and use it for all relevant services.
- [x] 2.2 Make `dev.sh` executable (`chmod +x dev.sh`).

## 3. Documentation
- [x] 3.1 Update `README.md` (or other setup docs) to reflect using `./dev.sh` as the standard way to run the local environment, and specify `https://fastjob.loca.lt` as the single domain.
- [x] 3.2 Ensure developers are instructed to install `tmux` if not already present.
