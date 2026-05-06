"""Test-only settings. Extends base settings but overrides slow / external deps."""
import os

os.environ.setdefault("SECRET_KEY", "test-key")
os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("DATABASE_URL", "postgres://x:x@x:5432/x")

from config.settings import *  # noqa: F401, F403, E402

# In-memory SQLite — fast, no fixtures to clean up.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Celery tasks run synchronously and re-raise exceptions.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# In-memory cache so each test process is isolated.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Rate limiting off during tests — we test it explicitly when needed.
RATELIMIT_ENABLE = False

# No real file uploads; plain static-files storage (avoids collectstatic).
# "private" alias is required by CV.file (storage="private").
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    "private": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
}

# Capture emails in memory.
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Faster password hashing during tests.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# No Sentry, no matter what the env says.
SENTRY_DSN = ""
