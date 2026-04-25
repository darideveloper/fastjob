# Monitoring & Testing

FastJob uses structured console logging (Docker/PaaS friendly), optional Sentry for error tracking, and a pytest suite covering the mailing engine and critical business logic.

---

## Health check — `/healthz`

A tiny endpoint for load balancers, uptime monitors (UptimeRobot, Pingdom, BetterStack), and container orchestrators. Implemented in `config/health.py`.

```bash
curl https://yourdomain.com/healthz
# → 200 {"status":"ok","db":true,"cache":true}
```

- Returns **200** only when both PostgreSQL and Redis are reachable.
- Returns **503** with the failing dependency flipped to `false` when either is down.
- Intentionally public (no auth) so external monitors can poll it without credentials.

**Why both DB and cache:** the cache is where rate limiting lives. If Redis is down the site technically stays up (thanks to `IGNORE_EXCEPTIONS=True`), but rate limiting is silently disabled — a health check that doesn't surface that is dishonest.

---

## Logging

### Configuration (`config/settings.py`)

```python
LOGGING = {
    "formatters": {
        "verbose": {"format": "[{asctime}] {levelname} {name} | {message}", "style": "{"},
    },
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "verbose"}},
    "root": {"handlers": ["console"], "level": config("LOG_LEVEL", default="INFO")},
    "loggers": {
        "django.db.backends": {"level": "WARNING"},   # suppress SQL query noise
        "apps.mailing": {"level": "INFO", "propagate": True},
        "apps.payments": {"level": "INFO", "propagate": True},
        "celery": {"level": "INFO", "propagate": True},
    },
}
```

All output goes to stdout/stderr. In Docker, this means `docker logs` or your log aggregator (Datadog, Loki, etc.) sees everything without additional configuration.

### Log format example

```
[2024-11-15 10:22:01,453] INFO apps.mailing.tasks | Sent CV: user=ana@gmail.com → company=acme@acme.es
[2024-11-15 10:22:05,901] WARNING apps.mailing.tasks | No eligible companies for user=bob@outlook.com
[2024-11-15 10:22:06,412] ERROR apps.mailing.tasks | Send failed for user=carlos@gmail.com: Gmail API error 429: ...
```

### Log level

Controlled by `LOG_LEVEL` env var. Values: `DEBUG`, `INFO`, `WARNING`, `ERROR`. Default: `INFO`.

Set `LOG_LEVEL=DEBUG` locally to see all Django internals (SQL queries, etc.) — don't use in production.

### What the engine logs

| Event | Level |
|---|---|
| Successful CV send | INFO |
| No eligible companies for a user | INFO |
| No active email templates | WARNING |
| Token expired, campaign paused | WARNING |
| Gmail/Graph send error | ERROR |
| Celery task start/stop (via `CELERY_TASK_TRACK_STARTED`) | INFO |

---

## Sentry

Sentry is opt-in: only initializes when `SENTRY_DSN` is set in `.env`. If left blank, no Sentry calls are made.

### Integrations enabled

| Integration | What it captures |
|---|---|
| `DjangoIntegration` | Unhandled exceptions in views, middleware |
| `CeleryIntegration` | Unhandled exceptions in Celery tasks |
| `LoggingIntegration` | Python `logging.ERROR`+ records → Sentry events |

### Config

| Env var | Default | Purpose |
|---|---|---|
| `SENTRY_DSN` | `""` (disabled) | Sentry project DSN |
| `SENTRY_ENVIRONMENT` | `"production"` | `environment` tag in Sentry |
| `SENTRY_RELEASE` | `""` | `release` tag (e.g. git SHA) — useful for release tracking |
| `SENTRY_TRACES_SAMPLE_RATE` | `0.1` | 10% of requests are traced for performance monitoring |

`send_default_pii=False` is hardcoded — OAuth tokens and email addresses are sensitive and must not be sent to Sentry.

---

## Testing

### Stack

| Library | Version | Role |
|---|---|---|
| `pytest` | 8.3.3 | Test runner |
| `pytest-django` | 4.9.0 | Django integration (settings, db fixtures) |
| `pytest-mock` | 3.14.0 | `mocker` fixture for mocking external calls |

Configuration in `pytest.ini`:

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
```

### Running the tests

```bash
# Full suite
pytest

# Specific app
pytest apps/mailing/tests/

# With coverage (if coverage is installed)
pytest --cov=apps
```

### Test coverage by app

### CI (GitHub Actions)

`.github/workflows/ci.yml` runs on every push and PR to `main`:

1. Install Python 3.12 and project dependencies.
2. `python manage.py check` — Django system check.
3. `python manage.py makemigrations --check --dry-run` — catches model changes that lack a migration.
4. `pytest -q` — full test suite.

CI uses `DJANGO_SETTINGS_MODULE=config.test_settings`, so it never needs a real Postgres or Redis — SQLite in-memory + locmem cache do the job.

---

**`apps/mailing/tests/` — 17+ tests**

`test_engine.py` — `send_cv_email` and token refresh:
- Happy-path Gmail send (mocks `requests.post`).
- Happy-path Microsoft Graph send.
- Token refresh needed + succeeds.
- Token refresh fails → `TokenExpiredError`.
- No linked OAuth account → `TokenExpiredError`.
- Gmail API returns 5xx → exception propagated.
- Graph API returns 5xx → exception propagated.
- Token still valid (no refresh needed).

`test_tasks.py` — `process_mailing_queue` business logic:
- Slow-drip: user sent recently → skipped.
- Blacklist: company blacklisted → skipped.
- Cooldown: company received recently → skipped.
- Area filter: company doesn't match → skipped.
- Token expired → campaign paused, notification dispatched.
- No credits → skipped.
- No CV → skipped.
- No active templates → warning logged, no sends.
- Happy path: email sent, credit deducted.

`test_views.py` — CV download and unsubscribe views:
- 404 on unknown `cv_download_token`.
- 404 when user has no CV file.
- Redirect to pre-signed URL on valid token (mocks `boto3.client`).
- 429 when rate limit exceeded.
- Unsubscribe creates `Blacklist` row.
- Unsubscribe is idempotent (second click → same row).

**`apps/companies/tests/` — 5+ tests**

`test_importers.py`:
- Empty file → error.
- Missing required column → error.
- Invalid email → per-row error, rest imports.
- Valid file → correct created/updated counts.
- Re-import → updates existing rows.

**`apps/payments/tests/`**

`test_webhook.py`:
- Invalid Stripe signature → 400.
- Valid event, `PENDING` payment → credits granted, status → `COMPLETED`.
- Duplicate webhook (already `COMPLETED`) → no-op, no extra credits.

### What is NOT tested

- End-to-end OAuth flows (requires mocking Google's server).
- Dashboard views (render tests exist implicitly via fixtures; no dedicated suite yet).
- Admin import view (tested manually via QA).

These are reasonable omissions given the cost of mocking OAuth and the simplicity of the views — the business logic lives in the engine/task layer, which is well-covered.

---

## Related docs

- [`mailing-engine.md`](mailing-engine.md) — the most test-covered module.
- [`security.md`](security.md) — Sentry `send_default_pii=False`.
