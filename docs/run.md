# Running Locally

This guide gets the full FastJob stack running on your machine: Django, PostgreSQL, Redis, Celery worker, and Celery beat.

---

## Prerequisites

| Tool | Min version | Notes |
|---|---|---|
| Python | 3.12 | Matches the Docker base image |
| Docker + Docker Compose | any recent | Optional — needed only for the DB/Redis shortcuts below |
| Git | any | |

---

## 1. Clone and create a virtualenv

```bash
git clone <repo-url> fastjob
cd fastjob

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`. The minimum set needed to start the server:

| Variable | What to put |
|---|---|
| `SECRET_KEY` | Any long random string (see below) |
| `DEBUG` | `True` |
| `DATABASE_URL` | Leave as `postgres://postgres:postgres@localhost:5432/fastjob` if using Docker below |
| `REDIS_URL` | `redis://localhost:6379/0` |
| `CACHE_REDIS_URL` | `redis://localhost:6379/1` |

Generate a `SECRET_KEY`:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**You can leave all other vars blank to start the server**, but features that depend on them won't work:
- OAuth login requires `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` (and/or Microsoft equivalents).
- CV upload requires `AWS_*` Spaces credentials.
- Payments require `STRIPE_*` keys.
- Notifications require SMTP credentials.

---

## 3. Start PostgreSQL and Redis

**Option A — Docker (recommended, nothing to install):**

```bash
docker compose up -d db redis
```

This starts only the database and Redis, leaving Django/Celery to run natively on your host. The DB is accessible at `localhost:5432`.

**Option B — native Postgres + Redis:**

Install and start both services yourself (via Homebrew, apt, etc.), then make sure the ports in `.env` match.

---

## 4. Run migrations and seed data

```bash
python manage.py migrate
python manage.py setup_periodic_tasks   # registers the Celery beat task
```

`setup_periodic_tasks` creates the `IntervalSchedule` (1 minute) and `PeriodicTask` row in the DB. Without it, Celery beat won't fire the mailing engine.

---

## 5. Create a superuser

```bash
python manage.py createsuperuser
```

You'll need this to access `/admin/` and to import companies.

---

## 6. Start all processes

You need four terminal windows (or use a process manager like `honcho`/`foreman` with a `Procfile`):

**Terminal 1 — Django dev server:**
```bash
python manage.py runserver
```
Django is now at [http://localhost:8000](http://localhost:8000).

**Terminal 2 — Celery worker:**
```bash
celery -A config worker -l info -c 4
```

**Terminal 3 — Celery beat:**
```bash
celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

**Terminal 4 — (optional) Stripe CLI for webhook forwarding:**
```bash
stripe listen --forward-to localhost:8000/payments/webhook/
```
Copy the printed webhook secret into `STRIPE_WEBHOOK_SECRET` in `.env`. Required only if testing payments locally.

---

## 7. Verify it's working

1. Open [http://localhost:8000/admin/](http://localhost:8000/admin/) — log in with the superuser you created.
2. Go to `Mailing → Configuración del Sistema` — you should see the singleton row.
3. Go to `Periodic Tasks → Periodic Tasks` — you should see `process_mailing_queue`.
4. Check the Celery worker terminal — you should see `[tasks]` listing registered tasks.

---

## Running with Docker Compose (full stack)

If you prefer everything containerised:

```bash
cp .env.example .env
# Edit .env as needed (SECRET_KEY at minimum)

docker compose up --build
```

This starts: `db`, `redis`, `web` (Gunicorn), `celery_worker`, `celery_beat`.

After the containers start:

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py setup_periodic_tasks
docker compose exec web python manage.py createsuperuser
```

Django is at [http://localhost:8000](http://localhost:8000).

**Note:** the `docker-compose.yml` mounts `.` into `/app` in the containers, so code changes reload automatically in `web` only if you switch the command to `runserver`. Gunicorn does not auto-reload.

---

## Running tests

```bash
pytest                          # full suite
pytest apps/mailing/tests/      # mailing engine + tasks only
pytest -x                       # stop on first failure
pytest -v                       # verbose output
```

Tests use a separate in-memory SQLite-compatible test database created by `pytest-django`. No real Postgres connection is required for the test suite.

---

## Setting up OAuth (Google)

To test the actual login flow locally:

1. Google Cloud Console → APIs & Services → Library → enable **Gmail API**.
2. OAuth consent screen → External → add `https://www.googleapis.com/auth/gmail.send` scope.
3. Credentials → Create OAuth 2.0 Client ID → Web application.
4. Authorized redirect URI: `http://localhost:8000/accounts/google/login/callback/`
5. Copy client ID + secret → `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` in `.env`.
6. Restart the dev server.

For Microsoft, see [`features/authentication.md`](features/authentication.md).

---

## Useful management commands

| Command | Purpose |
|---|---|
| `python manage.py migrate` | Apply DB migrations |
| `python manage.py setup_periodic_tasks` | Register Celery beat tasks |
| `python manage.py createsuperuser` | Create an admin user |
| `python manage.py collectstatic` | Gather static files (needed for production) |
| `python manage.py shell_plus` | Enhanced shell (via `django-extensions`) |

---

## Environment variable reference

See `.env.example` for the full annotated list. All variables are also documented inline in the feature docs and aggregated in [`deploy.md`](deploy.md).
