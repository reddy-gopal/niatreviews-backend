import os
import importlib.util

from .base import *


def env_list(name):
    return [value.strip() for value in os.getenv(name, "").split(",") if value.strip()]


DEBUG = False
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS")
SECURE_HSTS_SECONDS = 31536000
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

json_formatter_class = (
    "pythonjsonlogger.jsonlogger.JsonFormatter"
    if importlib.util.find_spec("pythonjsonlogger")
    else "logging.Formatter"
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": json_formatter_class,
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
