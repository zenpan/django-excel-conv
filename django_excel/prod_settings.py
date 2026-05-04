import os

from .settings import *  # noqa: F403


def env_list(name, default):
    raw_value = os.environ.get(name)
    if not raw_value:
        return default
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def env_bool(name, default=False):
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    return raw_value.lower() in {"1", "true", "yes", "on"}


DEBUG = env_bool("DJANGO_DEBUG", False)
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", SECRET_KEY)  # noqa: F405
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", ["excel.doyagalawfirm.com"])
CSRF_TRUSTED_ORIGINS = env_list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    ["https://excel.doyagalawfirm.com"],
)

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_SECURE_HSTS_SECONDS", "3600"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS",
    False,
)
SECURE_HSTS_PRELOAD = env_bool("DJANGO_SECURE_HSTS_PRELOAD", False)
SILENCED_SYSTEM_CHECKS = ["security.W005", "security.W021"]

STATICFILES_DIRS = [BASE_DIR / "static"]  # noqa: F405
STATIC_ROOT = os.environ.get(
    "DJANGO_STATIC_ROOT",
    "/var/www/excel.doyagalawfirm.com/static",
)

db_engine = os.environ.get("DJANGO_DB_ENGINE", "django.db.backends.sqlite3")

DATABASES = {
    "default": {
        "ENGINE": db_engine,
        "NAME": os.environ.get("DJANGO_DB_NAME", BASE_DIR / "db.sqlite3"),  # noqa: F405
    }
}

if db_engine != "django.db.backends.sqlite3":
    DATABASES["default"].update(
        {
            "USER": os.environ.get("DJANGO_DB_USER", "django_excel"),
            "PASSWORD": os.environ.get("DJANGO_DB_PASSWORD", "django_excel"),
            "HOST": os.environ.get("DJANGO_DB_HOST", "localhost"),
            "PORT": os.environ.get("DJANGO_DB_PORT", "5432"),
        }
    )
