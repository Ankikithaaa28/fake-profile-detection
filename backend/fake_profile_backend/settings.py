"""
Django settings for the fake_profile_backend project.

Secrets and machine-specific values are read from environment variables
(or a `.env` file in the project root). See `.env.example` and README.md.
"""
from pathlib import Path

import environ

# Project root (the folder that contains `backend/`, `.env` and `db.sqlite3`)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
if (BASE_DIR / ".env").exists():
    environ.Env.read_env(BASE_DIR / ".env")

# ---------------------------------------------------------------------------
# X (Twitter) API credentials - OPTIONAL.
# Email and Instagram detection work without them; only the X page needs a
# bearer token. Never commit real values (see .gitignore).
# ---------------------------------------------------------------------------
FAKEPROFILE_API_KEY = env("FAKEPROFILE_API_KEY", default="")
FAKEPROFILE_API_SECRET_KEY = env("FAKEPROFILE_API_SECRET_KEY", default="")
FAKEPROFILE_ACCESS_TOKEN = env("FAKEPROFILE_ACCESS_TOKEN", default="")
FAKEPROFILE_ACCESS_TOKEN_SECRET = env("FAKEPROFILE_ACCESS_TOKEN_SECRET", default="")
FAKEPROFILE_BEARER_TOKEN = env("FAKEPROFILE_BEARER_TOKEN", default="")

# ---------------------------------------------------------------------------
# Core security settings - safe defaults for local development.
# For any real deployment set DJANGO_SECRET_KEY, DJANGO_DEBUG=False and
# DJANGO_ALLOWED_HOSTS in the environment.
# ---------------------------------------------------------------------------
SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-only-insecure-key-change-me")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1", ".vercel.app", ".vercel.app/"])

# TEMPORARY: let unhandled exceptions reach the WSGI entry point so the
# failure is visible in the response body. Remove once deployment is stable.
DEBUG_PROPAGATE_EXCEPTIONS = True

# ---------------------------------------------------------------------------
# Application definition
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "fake_profile_backend",
    "instagram",
    "email_detector",
    # "facebook",  # placeholder app - not implemented yet
    "x",
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

ROOT_URLCONF = "fake_profile_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "backend" / "templates"],
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

WSGI_APPLICATION = "fake_profile_backend.wsgi.application"

# ---------------------------------------------------------------------------
# Database (SQLite file is created by `python manage.py migrate`)
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "backend" / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-signal",
    }
}
