# Python modules
import os
from datetime import timedelta
from decouple import config


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ----------------------------------------------
# Env id
#
ENV_POSSIBLE_OPTIONS = (
    "local",
    "prod",
)
ENV_ID = config("PROJECT_ENV_ID")
SECRET_KEY = config("DJANGO_SECRET_KEY")

# ----------------------------------------------
# DJANGO REST FRAMEWORK
#

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PAGINATION_CLASS": "apps.blog.pagination.CustomCursorPagination",
    "PAGE_SIZE": 10,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=12),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
}

# ----------------------------------------------
# LOGGING
#

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    # Filters
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        }
    },
    # Formatters
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} : {module} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} ",
            "style": "{",
        },
    },
    # Handlers
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simple",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "WARNING",
            "filename": os.path.join(BASE_DIR, "logs/app.log"),
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 3,
            "formatter": "verbose",
        },
        "debug_only_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "filename": os.path.join(BASE_DIR, "logs/debug_requests.log"),
            "filters": ["require_debug_true"],
            "formatter": "verbose",
        },
    },
    # Loggers
    "loggers": {
        "users": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "blog": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["file"],
            "level": "WARNING",
            "propagate": False,
        },
        "debug_requests": {
            "handlers": ["debug_only_file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# ----------------------------------------------
# REDIS
#

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}
