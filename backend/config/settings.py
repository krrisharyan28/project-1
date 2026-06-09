"""
Django settings for the AI Fraud Alert Dashboard.

Configuration is driven entirely by environment variables (loaded from `.env`
in development). The stack is strict: PostgreSQL and Ollama are required —
there is no SQLite or offline-AI fallback.
"""
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

import os

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env (development). In production, real environment variables take over.
load_dotenv(BASE_DIR / ".env")


# --------------------------------------------------------------------------- #
# Small env helpers
# --------------------------------------------------------------------------- #
def env(key: str, default: str | None = None) -> str | None:
    return os.environ.get(key, default)


def env_bool(key: str, default: bool = False) -> bool:
    return env(key, str(default)).lower() in {"1", "true", "yes", "on"}


def env_int(key: str, default: int) -> int:
    return int(env(key, str(default)))


def env_list(key: str, default: str = "") -> list[str]:
    raw = env(key, default) or ""
    return [item.strip() for item in raw.split(",") if item.strip()]


# --------------------------------------------------------------------------- #
# Core
# --------------------------------------------------------------------------- #
SECRET_KEY = env("DJANGO_SECRET_KEY", "insecure-dev-key-change-me")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    "django_filters",
    # Local apps
    "apps.accounts",
    "apps.transactions",
    "apps.fraud",
    "apps.ai",
    "apps.core",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# --------------------------------------------------------------------------- #
# Database — PostgreSQL only (strict stack)
# --------------------------------------------------------------------------- #
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", "fraud_dashboard"),
        "USER": env("POSTGRES_USER", "fraud"),
        "PASSWORD": env("POSTGRES_PASSWORD", "fraud"),
        "HOST": env("POSTGRES_HOST", "localhost"),
        "PORT": env("POSTGRES_PORT", "5432"),
    }
}


# --------------------------------------------------------------------------- #
# Auth
# --------------------------------------------------------------------------- #
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# --------------------------------------------------------------------------- #
# Django REST Framework + JWT
# --------------------------------------------------------------------------- #
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "common.pagination.DefaultPagination",
    "PAGE_SIZE": env_int("API_PAGE_SIZE", 20),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "EXCEPTION_HANDLER": "common.exceptions.api_exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env_int("JWT_ACCESS_MINUTES", 30)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env_int("JWT_REFRESH_DAYS", 7)),
    "AUTH_HEADER_TYPES": ("Bearer",),
}


# --------------------------------------------------------------------------- #
# CORS
# --------------------------------------------------------------------------- #
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost:5173")


# --------------------------------------------------------------------------- #
# Ollama / Llama-3 (required)
# --------------------------------------------------------------------------- #
OLLAMA_BASE_URL = env("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = env("OLLAMA_MODEL", "llama3")
OLLAMA_TIMEOUT_SECONDS = env_int("OLLAMA_TIMEOUT_SECONDS", 60)


# --------------------------------------------------------------------------- #
# Fraud engine thresholds (tunable without code changes)
# --------------------------------------------------------------------------- #
FRAUD = {
    "HIGH_AMOUNT_THRESHOLD": env_int("FRAUD_HIGH_AMOUNT_THRESHOLD", 10000),
    "NEW_CARD_AMOUNT_THRESHOLD": env_int("FRAUD_NEW_CARD_AMOUNT_THRESHOLD", 2000),
    "VELOCITY_COUNT": env_int("FRAUD_VELOCITY_COUNT", 3),
    "VELOCITY_WINDOW_MINUTES": env_int("FRAUD_VELOCITY_WINDOW_MINUTES", 10),
}


# --------------------------------------------------------------------------- #
# Uploads / I18N / static
# --------------------------------------------------------------------------- #
MAX_UPLOAD_MB = env_int("MAX_UPLOAD_MB", 10)
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_MB * 1024 * 1024

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
