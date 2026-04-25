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
    # Third-party
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.microsoft",
    "storages",
    "django_celery_beat",
    # Local
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
DATABASES = {
    "default": config(
        "DATABASE_URL",
        default="postgres://postgres:@localhost:5432/faztjob",
        cast=dj_database_url.parse
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTH_USER_MODEL = "accounts.User"

LANGUAGE_CODE = config("LANGUAGE_CODE", default="es")
TIME_ZONE = config("TIME_ZONE", default="Europe/Madrid")
USE_I18N = config("USE_I18N", default=True, cast=bool)
USE_TZ = config("USE_TZ", default=True, cast=bool)

# Static files
STATIC_URL = config("STATIC_URL", default="/static/")
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SITE_ID = config("SITE_ID", default=1, cast=int)
SITE_DOMAIN = config("SITE_DOMAIN", default="localhost:8000")
SITE_NAME = config("SITE_NAME", default="ResumeLink")

# Authentication
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

LOGIN_URL = config("LOGIN_URL", default="/accounts/login/")
LOGIN_REDIRECT_URL = config("LOGIN_REDIRECT_URL", default="/dashboard/")
LOGOUT_REDIRECT_URL = config("LOGOUT_REDIRECT_URL", default="/")
ACCOUNT_LOGOUT_REDIRECT_URL = config("ACCOUNT_LOGOUT_REDIRECT_URL", default="/")

# django-allauth
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = config("ACCOUNT_EMAIL_VERIFICATION", default="none")
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_USERNAME_REQUIRED = False
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_ADAPTER = "apps.accounts.adapters.SocialAccountAdapter"

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": config("GOOGLE_CLIENT_ID", default=""),
            "secret": config("GOOGLE_CLIENT_SECRET", default=""),
        },
        "SCOPE": [
            "openid",
            "email",
            "profile",
            "https://www.googleapis.com/auth/gmail.send",
        ],
        "AUTH_PARAMS": {"access_type": "offline", "prompt": "consent"},
        "FETCH_USERINFO": True,
    },
    "microsoft": {
        "APP": {
            "client_id": config("MICROSOFT_CLIENT_ID", default=""),
            "secret": config("MICROSOFT_CLIENT_SECRET", default=""),
        },
        "SCOPE": ["Mail.Send", "User.Read", "offline_access"],
        "AUTH_PARAMS": {"prompt": "consent"},
    },
}

# DigitalOcean Spaces (S3 Compatible)
AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY", default="")
AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME", default="faztjob")
AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME", default="nyc3")
AWS_S3_ENDPOINT_URL = config("AWS_S3_ENDPOINT_URL", default="https://nyc3.digitaloceanspaces.com")
AWS_S3_CUSTOM_DOMAIN = config("AWS_S3_CUSTOM_DOMAIN", default="")
AWS_DEFAULT_ACL = "private"
AWS_S3_FILE_OVERWRITE = False
AWS_QUERYSTRING_AUTH = True
AWS_QUERYSTRING_EXPIRE = 300  # 5 minutes for signed CV URLs

DEFAULT_FILE_STORAGE = config("DEFAULT_FILE_STORAGE", default="storages.backends.s3boto3.S3Boto3Storage")

# Celery
CELERY_BROKER_URL = config("REDIS_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = config("REDIS_URL", default="redis://localhost:6379/0")
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_TASK_TRACK_STARTED = True

# Stripe
STRIPE_PUBLIC_KEY = config("STRIPE_PUBLIC_KEY", default="")
STRIPE_SECRET_KEY = config("STRIPE_SECRET_KEY", default="")
STRIPE_WEBHOOK_SECRET = config("STRIPE_WEBHOOK_SECRET", default="")

# Email (system notifications only)
EMAIL_BACKEND = config("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="ResumeLink <noreply@example.com>")

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
SESSION_COOKIE_AGE = config("SESSION_COOKIE_AGE", default=604800, cast=int)  # 1 week
CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", default=False, cast=bool)
CSRF_COOKIE_HTTPONLY = config("CSRF_COOKIE_HTTPONLY", default=True, cast=bool)

# Hard caps on request body size (defense in depth alongside Nginx + view-level checks).
# DATA_UPLOAD_MAX_MEMORY_SIZE limits non-file form data per request; multipart file
# bytes are excluded from this counter (the 10 MB CV cap is enforced in upload_cv).
DATA_UPLOAD_MAX_MEMORY_SIZE = config("DATA_UPLOAD_MAX_MEMORY_SIZE", default=5 * 1024 * 1024, cast=int)
FILE_UPLOAD_MAX_MEMORY_SIZE = config("FILE_UPLOAD_MAX_MEMORY_SIZE", default=5 * 1024 * 1024, cast=int)
SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=0, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False, cast=bool)
SECURE_HSTS_PRELOAD = config("SECURE_HSTS_PRELOAD", default=False, cast=bool)
SECURE_CONTENT_TYPE_NOSNIFF = config("SECURE_CONTENT_TYPE_NOSNIFF", default=True, cast=bool)
SECURE_REFERRER_POLICY = config("SECURE_REFERRER_POLICY", default="strict-origin-when-cross-origin")
X_FRAME_OPTIONS = config("X_FRAME_OPTIONS", default="DENY")
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="", cast=Csv())

# Tells Django it's behind a TLS-terminating proxy (DO App Platform, Heroku, Nginx).
if config("TRUST_PROXY_SSL_HEADER", default=False, cast=bool):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ---------------------------------------------------------------------------
# Rate limiting — we raise the django-ratelimit exception to a friendly 429.
# Decorators: see apps/mailing/views.py.
# ---------------------------------------------------------------------------
RATELIMIT_ENABLE = config("RATELIMIT_ENABLE", default=True, cast=bool)
