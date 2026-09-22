"""
Django settings for the parcel-application-portal project.

Single env-var-driven settings module (django-environ) rather than a
settings/base|dev|prod split — every tunable comes from an env var with a
sane default, same pattern as dice-document-pipeline-api.
"""

from pathlib import Path

import environ
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env.str("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# Error monitoring — an empty SENTRY_DSN (the default; not set up yet) makes the SDK a
# no-op, so this is safe to leave wired up unconditionally rather than gating it behind
# an extra "is monitoring enabled" flag. See common/services.py's LoggingService, the
# only other place in the project that should import sentry_sdk directly.
sentry_sdk.init(
    dsn=env.str("SENTRY_DSN", default=""),
    integrations=[DjangoIntegration()],
    environment=env.str("SENTRY_ENVIRONMENT", default="development"),
    send_default_pii=False,
)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_tasks",
    "django_tasks_db",
    "crispy_forms",
    "crispy_bootstrap5",
    "guardian",
    "django_fsm_log",
    "common",
    "templates",
    "addresses",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases
DATABASES = {
    "default": env.db_url("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/
STATIC_URL = "static/"

# Media / object storage
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Unset S3_BUCKET_NAME (the default) keeps local FileSystemStorage. Set it to point
# at a real S3-style bucket in prod, or at a local Garage container in dev (see
# README's "Media storage (Garage)" section for one-time setup).
S3_BUCKET_NAME = env.str("S3_BUCKET_NAME", default="")
STORAGES = {
    "default": (
        {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "bucket_name": S3_BUCKET_NAME,
                "endpoint_url": env.str("S3_ENDPOINT_URL", default=None),
                "access_key": env.str("S3_ACCESS_KEY", default=""),
                "secret_key": env.str("S3_SECRET_KEY", default=""),
                "region_name": env.str("S3_REGION_NAME", default="auto"),
                "signature_version": env.str("S3_SIGNATURE_VERSION", default="s3v4"),
                "addressing_style": env.str("S3_ADDRESSING_STYLE", default="virtual"),
            },
        }
        if S3_BUCKET_NAME
        else {"BACKEND": "django.core.files.storage.FileSystemStorage"}
    ),
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# Background tasks (django-tasks core API). django-tasks-db (the DatabaseBackend,
# INSTALLED_APPS entry, migrations, and the `worker` service in docker-compose.yml
# running `manage.py db_worker`) is installed and ready, but not the default — tasks
# run synchronously in-process via ImmediateBackend until TASKS_BACKEND is set.
# Flip it with:
#   TASKS_BACKEND=django_tasks_db.DatabaseBackend
TASKS = {
    "default": {
        "BACKEND": env.str(
            "TASKS_BACKEND", default="django_tasks.backends.immediate.ImmediateBackend"
        ),
    },
}

# crispy-forms
CRISPY_TEMPLATE_PACK = "bootstrap5"
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
