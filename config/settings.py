from pathlib import Path

from decouple import config, Csv
import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY", default="django-insecure-changeme-in-production")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

# Fail-closed: refuse to boot in production with the placeholder SECRET_KEY.
if not DEBUG and SECRET_KEY.startswith("django-insecure"):
    raise ImproperlyConfigured("SECRET_KEY must be set in production.")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.humanize",
    # Third-party
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.microsoft",
    "storages",
    "django_celery_beat",
    # Local
    "apps.core",
    "apps.accounts",
    "apps.companies",
    "apps.mailing",
    "apps.payments",
    "apps.dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "apps.mailing.middleware.RatelimitMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database
# dj_database_url.config() automatically looks for the DATABASE_URL env var.
# We use decouple's config() to provide a fallback only if needed.
DATABASES = {
    "default": dj_database_url.config(
        default=config("DATABASE_URL", default="postgres://postgres:postgres@localhost:9001/fastjob"),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTH_USER_MODEL = "accounts.User"

LANGUAGE_CODE = "es"
TIME_ZONE = "Europe/Madrid"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SITE_ID = 1
SITE_DOMAIN = config("SITE_DOMAIN", default="localhost")
SITE_NAME = config("SITE_NAME", default="FastJob")
# H12: scheme used to build absolute URLs in outbound emails and Stripe
# return URLs. Decoupled from DEBUG so a developer running with DEBUG=True
# behind an HTTPS-terminating proxy still emits `https://` links.
SITE_SCHEME = config("SITE_SCHEME", default="https")

# Authentication
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/"
ACCOUNT_LOGOUT_REDIRECT_URL = "/"

# django-allauth
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_USERNAME_REQUIRED = False
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_ADAPTER = "apps.accounts.adapters.SocialAccountAdapter"
SOCIALACCOUNT_STORE_TOKENS = True

# OAuth operational guardrails — see openspec/specs/mailing/spec.md.
# Set GOOGLE_OAUTH_PROJECT_MODE=testing if the Google Cloud OAuth consent screen
# is still in "Testing" status — the /healthz endpoint will surface a warning so
# the 7-day refresh-token expiry does not silently brick long-running campaigns.
GOOGLE_OAUTH_PROJECT_MODE = config("GOOGLE_OAUTH_PROJECT_MODE", default="production")
# Microsoft tenant segment used in the token endpoint URL. "common" supports
# multi-tenant + personal accounts; set to a tenant GUID for single-tenant apps.
MICROSOFT_TENANT = config("MICROSOFT_TENANT", default="common")

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": [
            "openid",
            "email",
            "profile",
            "https://www.googleapis.com/auth/gmail.modify",
        ],
        "AUTH_PARAMS": {"access_type": "offline", "prompt": "consent"},
        "FETCH_USERINFO": True,
    },
    "microsoft": {
        "SCOPE": ["Mail.Send", "User.Read", "offline_access"],
        "AUTH_PARAMS": {"prompt": "consent"},
    },
}

# DigitalOcean Spaces (S3 Compatible)
AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY", default="")
AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME", default="fastjob")
AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME", default="nyc3")
AWS_S3_ENDPOINT_URL = config("AWS_S3_ENDPOINT_URL", default="https://nyc3.digitaloceanspaces.com")
AWS_S3_CUSTOM_DOMAIN = config("AWS_S3_CUSTOM_DOMAIN", default="")
AWS_DEFAULT_ACL = "private"
AWS_S3_FILE_OVERWRITE = False
AWS_QUERYSTRING_AUTH = True
AWS_QUERYSTRING_EXPIRE = 300  # 5 minutes for signed CV URLs

import os

# Company import local filesystem settings (shared between web and celery_worker via Docker volume)
COMPANY_IMPORT_LOCAL_PATH = config("COMPANY_IMPORT_LOCAL_PATH", default=str(BASE_DIR / "imports"))
COMPANY_IMPORT_MAX_FILE_MB = config("COMPANY_IMPORT_MAX_FILE_MB", default=100, cast=int)
COMPANY_IMPORT_FILE_RETENTION_DAYS = config("COMPANY_IMPORT_FILE_RETENTION_DAYS", default=7, cast=int)
COMPANY_IMPORT_CHUNK_SIZE = config("COMPANY_IMPORT_CHUNK_SIZE", default=1000, cast=int)
COMPANY_IMPORT_PRESIGN_EXPIRY_SECONDS = config("COMPANY_IMPORT_PRESIGN_EXPIRY_SECONDS", default=600, cast=int)

# Storage settings
STORAGE_AWS = config("STORAGE_AWS", default=False, cast=bool)

if STORAGE_AWS:
    # 1. Credentials
    AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID", default="")
    AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY", default="")
    AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME", default="")

    # 2. Regional Settings
    AWS_S3_ENDPOINT_URL = config("AWS_S3_ENDPOINT_URL", default="")
    AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME", default="")

    # 3. Domain/CDN settings
    AWS_S3_CUSTOM_DOMAIN = config("AWS_S3_CUSTOM_DOMAIN", default="")

    # 4. Folder isolation
    AWS_PROJECT_FOLDER = config("AWS_PROJECT_FOLDER", default="fastjob")

    # 5. File Locations
    STATIC_LOCATION = f"{AWS_PROJECT_FOLDER}/static"
    PUBLIC_MEDIA_LOCATION = f"{AWS_PROJECT_FOLDER}/media"
    PRIVATE_MEDIA_LOCATION = f"{AWS_PROJECT_FOLDER}/private"
    IMPORTS_LOCATION = f"{AWS_PROJECT_FOLDER}/imports"

    # 6. Django-Storages Engine Mapping (Django 4.2+)
    STORAGES = {
        "default": {
            "BACKEND": "config.storage_backends.PublicMediaStorage",
        },
        "staticfiles": {
            "BACKEND": "config.storage_backends.StaticStorage",
        },
        "private": {
            "BACKEND": "config.storage_backends.PrivateMediaStorage",
        },
        "imports": {
            "BACKEND": "config.storage_backends.ImportsStorage",
        },
    }

    # 7. Optimization & Security
    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
    AWS_DEFAULT_ACL = None
else:
    # Fallback to local storage for development
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
        "private": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "imports": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
            "OPTIONS": {"location": COMPANY_IMPORT_LOCAL_PATH, "base_url": None},
        },
    }

# Celery
CELERY_BROKER_URL = config("REDIS_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = config("REDIS_URL", default="redis://localhost:6379/0")
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_TASK_TRACK_STARTED = True
CELERY_WORKER_CONCURRENCY = config("CELERY_WORKER_CONCURRENCY", default=4, cast=int)

# Stripe
STRIPE_PUBLIC_KEY = config("STRIPE_PUBLIC_KEY", default="")
STRIPE_SECRET_KEY = config("STRIPE_SECRET_KEY", default="")
STRIPE_WEBHOOK_SECRET = config("STRIPE_WEBHOOK_SECRET", default="")

# Email (system notifications only)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=False, cast=bool)
EMAIL_USE_SSL = config("EMAIL_USE_SSL", default=False, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="FastJob <noreply@example.com>")

# ---------------------------------------------------------------------------
# Cache (Redis) — required by django-ratelimit; reuses the Celery Redis instance
# on db 1 so cache eviction never affects the task queue on db 0.
# ---------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config("CACHE_REDIS_URL", default="redis://localhost:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,  # survive Redis blips in prod
        },
    }
}

# ---------------------------------------------------------------------------
# Logging — structured, console-based (Docker/PaaS friendly). Sentry captures
# ERROR+ automatically via its Django integration below.
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} | {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": config("LOG_LEVEL", default="INFO"),
    },
    "loggers": {
        "django.db.backends": {"level": "WARNING"},  # silence query noise
        "apps.mailing": {"level": "INFO", "propagate": True},
        "apps.payments": {"level": "INFO", "propagate": True},
        "celery": {"level": "INFO", "propagate": True},
    },
}

# ---------------------------------------------------------------------------
# Sentry — only initializes if SENTRY_DSN is set. Celery tasks and Django
# request errors are captured automatically.
# ---------------------------------------------------------------------------
SENTRY_DSN = config("SENTRY_DSN", default="")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            LoggingIntegration(level=None, event_level="ERROR"),
        ],
        environment=config("SENTRY_ENVIRONMENT", default="production"),
        release=config("SENTRY_RELEASE", default=""),
        traces_sample_rate=config("SENTRY_TRACES_SAMPLE_RATE", default=0.1, cast=float),
        send_default_pii=False,  # OAuth tokens + emails are sensitive
    )

# ---------------------------------------------------------------------------
# Production security headers — ALL env-gated so local dev is unaffected.
# Flip these on once you're behind HTTPS in production.
# ---------------------------------------------------------------------------
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=False, cast=bool)
SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", default=False, cast=bool)
SESSION_COOKIE_AGE = 604800  # 1 week (default Django: 2 weeks)
CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", default=False, cast=bool)
CSRF_COOKIE_HTTPONLY = True  # No client JS reads the CSRF token in this app

# Hard caps on request body size (defense in depth alongside Nginx + view-level checks).
# DATA_UPLOAD_MAX_MEMORY_SIZE limits non-file form data per request.
# Company imports now upload directly to object storage (presigned PUT), so
# Django never receives the .xlsx body — this can return to a sane default.
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB (covers CV uploads)
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5 MB streamed-to-disk threshold
SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=0, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False, cast=bool)
SECURE_HSTS_PRELOAD = config("SECURE_HSTS_PRELOAD", default=False, cast=bool)  # one-way door
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="http://localhost", cast=Csv())

# Verify essential configuration
if not ALLOWED_HOSTS or not CSRF_TRUSTED_ORIGINS or not SITE_DOMAIN:
    raise ImproperlyConfigured("ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, and SITE_DOMAIN must be set.")


# Tells Django it's behind a TLS-terminating proxy (DO App Platform, Heroku, Nginx).
if config("TRUST_PROXY_SSL_HEADER", default=False, cast=bool):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ---------------------------------------------------------------------------
# Rate limiting — we raise the django-ratelimit exception to a friendly 429.
# Decorators: see apps/mailing/views.py.
# ---------------------------------------------------------------------------
RATELIMIT_ENABLE = config("RATELIMIT_ENABLE", default=True, cast=bool)
