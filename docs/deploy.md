# Deploying to Production

This guide covers a production deployment using Docker Compose on a single VPS (DigitalOcean Droplet, Hetzner, etc.) behind Nginx as a TLS-terminating reverse proxy. The same principles apply to PaaS platforms (DigitalOcean App Platform, Railway, Render) with minor adjustments.

---

## Architecture

```
Internet
   │ HTTPS :443
   ▼
Nginx (TLS termination, static files)
   │ HTTP :8000
   ▼
Gunicorn (3 workers)    ◄── Docker service: web
   │
   ├── PostgreSQL        ◄── Managed DB (external) or Docker service: db
   ├── Redis             ◄── Managed Redis (external) or Docker service: redis
   ├── Celery Worker     ◄── Docker service: celery_worker
   └── Celery Beat       ◄── Docker service: celery_beat (exactly 1 instance)
```

**Recommendation:** use managed PostgreSQL and Redis from your cloud provider. Self-hosted DB/Redis are fine for small-scale but require you to handle backups, patching, and failover.

---

## Prerequisites

- A server with Docker + Docker Compose installed.
- A domain name pointed at the server's IP.
- TLS certificate (Let's Encrypt via Certbot is free and automatic).
- A DigitalOcean Spaces bucket (or any S3-compatible storage).
- Stripe account with a production webhook configured.
- Google and/or Microsoft OAuth app with production redirect URIs.

---

## Deploying to Coolify (One-Click)

FastJob is optimized for [Coolify](https://coolify.io), a self-hosted PaaS. The project includes a "one-click ready" `docker-compose.yml` that handles SSL, reverse proxying, and service discovery automatically.

### 1. Import the repository
1.  In Coolify, go to **Resources** -> **New Resource**.
2.  Select **Public Repository** or **Private Repository**.
3.  Enter the URL of this repository.
4.  Coolify will automatically detect the `docker-compose.yml` and its metadata.

### 2. Configure Environment Variables
Upon import, Coolify will parse the `environment` sections and prompt you for the following mandatory variables (marked with a red border in the UI):

| Variable | Description |
|---|---|
| `SECRET_KEY` | A long, random string for Django security. |
| `AWS_ACCESS_KEY_ID` | DigitalOcean Spaces access key. |
| `AWS_SECRET_ACCESS_KEY` | DigitalOcean Spaces secret key. |
| `AWS_STORAGE_BUCKET_NAME` | Your S3-compatible bucket name. |
| `STRIPE_PUBLIC_KEY` | Stripe frontend key (`pk_live_...`). |
| `STRIPE_SECRET_KEY` | Stripe backend key (`sk_live_...`). |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret. |
| `EMAIL_HOST` | Your SMTP server (e.g., `smtp.gmail.com`). |
| `EMAIL_HOST_USER` | SMTP username. |
| `EMAIL_HOST_PASSWORD` | SMTP password or App Password. |
| `DEFAULT_FROM_EMAIL` | The "From" address for system notifications. |
| `FLOWER_BASIC_AUTH` | Credentials for the Flower dashboard (`user:password`). |

**Coolify Magic Variables:**
The following are handled automatically by Coolify and do not require manual entry:
- `SERVICE_FQDN_WEB_8000`: Your dynamic deployment domain (e.g., `fastjob.es`).
- `SERVICE_URL_WEB_8000`: Your dynamic deployment URL with protocol (e.g., `https://fastjob.es`).
- `SERVICE_USER_POSTGRES` & `SERVICE_PASSWORD_POSTGRES`: Generated database credentials.
- `COOLIFY_VOLUME_POSTGRES_DATA`: Managed persistent storage for the database.

### 3. Deploy
Click **Deploy**. Coolify will build the image, provision the PostgreSQL and Redis containers, and start the stack.

### 4. Post-Deployment Setup
Once the `web` container is healthy, run the initialization commands via the Coolify terminal or `docker exec`:

```bash
python manage.py migrate
python manage.py setup_periodic_tasks
python manage.py createsuperuser
```

---

## Deploying to VPS (Manual Docker Compose)

```bash
# On the server
git clone <repo-url> /opt/fastjob
cd /opt/fastjob
```

---

## 2. Production `.env`

Copy `.env.example` to `.env` and fill in every variable. **Never commit `.env` to version control.**

```bash
cp .env.example .env
nano .env
```

### Critical values that differ from local dev

| Variable | Production value |
|---|---|
| `SECRET_KEY` | Long random string (50+ chars); generate fresh |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `yourdomain.com,www.yourdomain.com` |
| `SITE_DOMAIN` | `yourdomain.com` |
| `DATABASE_URL` | Connection string to managed PostgreSQL |
| `REDIS_URL` | Connection string to managed Redis (db 0) |
| `CACHE_REDIS_URL` | Same Redis host, db 1 (e.g. `redis://.../:1`) |
| `SECURE_SSL_REDIRECT` | `True` |
| `SESSION_COOKIE_SECURE` | `True` |
| `CSRF_COOKIE_SECURE` | `True` |
| `SECURE_HSTS_SECONDS` | `31536000` |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` | `True` |
| `TRUST_PROXY_SSL_HEADER` | `True` (Django is behind Nginx) |
| `CSRF_TRUSTED_ORIGINS` | `https://yourdomain.com` |
| `RATELIMIT_ENABLE` | `True` |
| `SENTRY_DSN` | Your Sentry project DSN |
| `SENTRY_ENVIRONMENT` | `production` |
| `STRIPE_SECRET_KEY` | Live key (`sk_live_...`) |
| `STRIPE_WEBHOOK_SECRET` | Live webhook secret |

### OAuth redirect URIs for production

**Google:** in Google Cloud Console, add `https://yourdomain.com/accounts/google/login/callback/`.

**Microsoft:** in Azure Portal app registration, add `https://yourdomain.com/accounts/microsoft/login/callback/`.

---

## 3. Build and start containers

```bash
docker compose up -d --build
```

Services started: `db` (if self-hosted), `redis` (if self-hosted), `web`, `celery_worker`, `celery_beat`.

---

## 4. First-deploy one-time setup

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py setup_periodic_tasks
docker compose exec web python manage.py createsuperuser
```

Run these **only once** on the first deploy. `migrate` is safe to re-run on subsequent deploys.

---

## 5. Nginx configuration

Install Nginx and Certbot, then create `/etc/nginx/sites-available/fastjob`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate     /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    include             /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam         /etc/letsencrypt/ssl-dhparams.pem;

    # Static files served by Whitenoise via Django — no separate /static/ block needed.

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
        client_max_body_size 15M;   # allow CV uploads up to 10 MB + overhead
    }
}
```

Enable and reload:

```bash
ln -s /etc/nginx/sites-available/fastjob /etc/nginx/sites-enabled/
certbot --nginx -d yourdomain.com -d www.yourdomain.com
nginx -t && systemctl reload nginx
```

---

## 6. Stripe webhook setup

1. Stripe Dashboard → Developers → Webhooks → Add endpoint.
2. Endpoint URL: `https://yourdomain.com/payments/webhook/`
3. Event to listen to: `checkout.session.completed`.
4. Copy the signing secret → `STRIPE_WEBHOOK_SECRET` in `.env`.
5. Restart the web container: `docker compose restart web`.

---

## 7. Verify production

```bash
# Check all containers are running
docker compose ps

# Check web logs for startup errors
docker compose logs web --tail=50

# Check Celery worker registered tasks
docker compose logs celery_worker --tail=30

# Check beat scheduler
docker compose logs celery_beat --tail=20
```

Open `https://yourdomain.com/admin/` and confirm:
- Login works.
- `Mailing → Periodic Tasks` shows `process_mailing_queue` with `Enabled = True`.
- `Mailing → Configuración del Sistema` shows the singleton row.

Check the health endpoint:

```bash
curl https://yourdomain.com/healthz
# {"status":"ok","db":true,"cache":true}
```

Point your uptime monitor (UptimeRobot / BetterStack / Pingdom) at `/healthz`. See [`features/monitoring.md`](features/monitoring.md) for details.

---

## Ongoing operations

### Deploying an update

```bash
git pull origin main
docker compose up -d --build
docker compose exec web python manage.py migrate   # only if migrations exist
```

Gunicorn picks up the new image when the `web` container is replaced. Zero-downtime is not guaranteed with this setup — for zero-downtime, consider a blue/green approach or a PaaS with built-in rolling deploys.

### Viewing logs in real time

```bash
docker compose logs -f web           # Django / Gunicorn
docker compose logs -f celery_worker # Celery task execution
docker compose logs -f celery_beat   # Beat scheduler ticks
```

### Backing up the database

The repo ships `scripts/backup_db.sh` — a `pg_dump | gzip | aws s3 cp` one-shot designed for nightly cron.

```bash
# /etc/cron.d/fastjob-backup
0 3 * * *  root  /opt/fastjob/scripts/backup_db.sh >> /var/log/fastjob-backup.log 2>&1
```

Required env vars (put them in `/etc/default/fastjob-backup` and `source` it in the cron line, or use `--env-file` if running inside Docker):

| Variable | Example |
|---|---|
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` | Managed PostgreSQL credentials |
| `BACKUP_BUCKET` | `fastjob-backups` (separate from your CV bucket) |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | Scoped to the backup bucket only |
| `AWS_S3_ENDPOINT_URL` | `https://nyc3.digitaloceanspaces.com` |

The script writes `fastjob-YYYYMMDD-HHMMSS.sql.gz` into `s3://$BACKUP_BUCKET/postgres/`. Set a **bucket lifecycle policy** to expire objects older than N days (DigitalOcean Spaces dashboard → Settings → Lifecycle rules) so the bucket doesn't grow forever.

Alternative: if you're using managed PostgreSQL from DigitalOcean / AWS RDS, enable the provider's built-in automated backups instead — they integrate with point-in-time recovery, which `pg_dump` does not.

### Celery task monitoring (Flower)

`docker-compose.yml` includes a `flower` service. It binds to `127.0.0.1:5555` only — the intent is that you reverse-proxy it through Nginx under a path like `/flower/` with HTTP Basic auth, not expose it to the internet directly.

`FLOWER_BASIC_AUTH` in `.env` sets the username/password (format: `user:password`). **Change the default `admin:changeme` before deploying.**

Nginx snippet to expose it:

```nginx
location /flower/ {
    proxy_pass http://127.0.0.1:5555/flower/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Flower gives visibility into queue depth, task history, failure rates, and per-task payloads — useful during incidents. It reveals task arguments (user IDs, company IDs) so never expose it unauthenticated.

### Scaling Celery workers

To handle more simultaneous users, increase concurrency or add more worker replicas:

```bash
# More slots per worker (edit .env or docker-compose.yml)
CELERY_WORKER_CONCURRENCY=8

# Or add a second worker container
docker compose up -d --scale celery_worker=2
```

**Never scale `celery_beat`** — exactly one beat process must run. Running two fires every periodic task twice.

### Continuous integration

`.github/workflows/ci.yml` runs on every push and PR:
- `manage.py check`
- `manage.py makemigrations --check --dry-run`
- `pytest -q`

No GitHub secrets are required — CI uses `config.test_settings` which is self-contained (SQLite in-memory, locmem cache, no external APIs). See [`features/monitoring.md`](features/monitoring.md#ci-github-actions) for details.

---

## Environment variable reference (production)

All variables from `.env.example` explained:

### Core Django

| Variable | Required | Purpose |
|---|---|---|
| `SECRET_KEY` | Yes | Cryptographic signing for sessions, CSRF, tokens |
| `DEBUG` | Yes | Must be `False` in production |
| `ALLOWED_HOSTS` | Yes | Comma-separated list of valid host headers |
| `SITE_DOMAIN` | Yes | Your domain (e.g., `fastjob.es`) |
| `SITE_NAME` | No | Default: `FastJob` |
| `SITE_SCHEME` | No | Default: `https` |

### Database

| Variable | Required | Purpose |
|---|---|---|
| `DATABASE_URL` | Yes | Unified connection string for Django |
| `DB_NAME` | Yes | Database name (required for backups) |
| `DB_USER` | Yes | Database user (required for backups) |
| `DB_PASSWORD` | Yes | Database password (required for backups) |
| `DB_HOST` | Yes | Database host (required for backups) |
| `DB_PORT` | No | Default: `5432` |

### Redis / Celery

| Variable | Required | Purpose |
|---|---|---|
| `REDIS_URL` | Yes | Celery broker + result backend (db 0) |
| `CACHE_REDIS_URL` | Yes | Django cache + rate limiting (db 1) |
| `CELERY_WORKER_CONCURRENCY` | No | Default: `4` |

### DigitalOcean Spaces

| Variable | Required | Purpose |
|---|---|---|
| `AWS_ACCESS_KEY_ID` | Yes | Spaces access key (scope to bucket only) |
| `AWS_SECRET_ACCESS_KEY` | Yes | Spaces secret key |
| `AWS_STORAGE_BUCKET_NAME` | Yes | Bucket name |
| `AWS_S3_REGION_NAME` | Yes | Region (e.g. `nyc3`, `ams3`) |
| `AWS_S3_ENDPOINT_URL` | Yes | `https://<region>.digitaloceanspaces.com` |
| `AWS_S3_CUSTOM_DOMAIN` | No | CDN domain if using Spaces CDN |
| `BACKUP_BUCKET` | Yes | Bucket for database backups |

### OAuth

| Variable | Required | Purpose |
|---|---|---|
| `GOOGLE_CLIENT_ID` | Yes (for Google) | OAuth app client ID |
| `GOOGLE_CLIENT_SECRET` | Yes (for Google) | OAuth app secret |
| `GOOGLE_OAUTH_PROJECT_MODE` | No | `production` or `testing` |
| `MICROSOFT_CLIENT_ID` | Yes (for Microsoft) | OAuth app client ID |
| `MICROSOFT_CLIENT_SECRET` | Yes (for Microsoft) | OAuth app secret |
| `MICROSOFT_TENANT` | No | Default: `common` |

### Stripe

| Variable | Required | Purpose |
|---|---|---|
| `STRIPE_PUBLIC_KEY` | Yes | Frontend publishable key |
| `STRIPE_SECRET_KEY` | Yes | Server-side secret key |
| `STRIPE_WEBHOOK_SECRET` | Yes | Webhook HMAC verification |

### Email (system notifications)

| Variable | Required | Purpose |
|---|---|---|
| `EMAIL_HOST` | Yes | SMTP host |
| `EMAIL_PORT` | No | Default: `587` |
| `EMAIL_USE_TLS` | No | Default: `True` |
| `EMAIL_HOST_USER` | Yes | SMTP username |
| `EMAIL_HOST_PASSWORD` | Yes | SMTP password / app password |
| `DEFAULT_FROM_EMAIL` | Yes | From header for system emails |

### Security

| Variable | Required | Purpose |
|---|---|---|
| `SECURE_SSL_REDIRECT` | Yes | `True` — redirect HTTP → HTTPS |
| `SESSION_COOKIE_SECURE` | Yes | `True` — HTTPS-only session cookie |
| `CSRF_COOKIE_SECURE` | Yes | `True` — HTTPS-only CSRF cookie |
| `SECURE_HSTS_SECONDS` | Yes | `31536000` for 1-year HSTS |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` | No | `True` recommended |
| `SECURE_HSTS_PRELOAD` | No | `True` only when ready for preload list |
| `TRUST_PROXY_SSL_HEADER` | Yes | `True` when behind Nginx/proxy |
| `CSRF_TRUSTED_ORIGINS` | Yes | `https://yourdomain.com` |

### Observability

| Variable | Required | Purpose |
|---|---|---|
| `LOG_LEVEL` | No | Default: `INFO` |
| `SENTRY_DSN` | No | Empty = Sentry disabled |
| `SENTRY_ENVIRONMENT` | No | Default: `production` |
| `SENTRY_RELEASE` | No | Git SHA or tag for release tracking |
| `SENTRY_TRACES_SAMPLE_RATE` | No | Default: `0.1` (10% of requests traced) |

### Rate limiting

| Variable | Required | Purpose |
|---|---|---|
| `RATELIMIT_ENABLE` | No | Default: `True` — set `False` only for testing |

---

## Related docs

- [`run.md`](run.md) — local development setup.
- [`features/security.md`](features/security.md) — security headers and threat model.
- [`features/monitoring.md`](features/monitoring.md) — logging and Sentry configuration.
