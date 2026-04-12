# Python modules
import os
from datetime import timedelta
from decouple import config


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_FROM_EMAIL = "r_garipova@kbtu.kz"

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
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Blog API",
    "DESCRIPTION": "API for a blog service",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=12),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "AUTH_HEADER_TYPES": ("JWT",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
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


# ------------------------------------------------
# Redis Configuration
#
REDIS_HOST = config("BLOG_REDIS_HOST", cast=str, default="localhost")
REDIS_PORT = config("BLOG_REDIS_PORT", cast=int, default=6379)
REDIS_CELERY_DB = config("BLOG_REDIS_CELERY_DB", cast=int, default=1)
BLOG_REDIS_DB = config("BLOG_REDIS_DB", cast=int, default=2)
REDIS_CHANNELS_DB = config("REDIS_CHANNELS_DB", cast=int, default=3)
REDIS_CACHE_DB = config("REDIS_CACHE_DB", cast=int, default=4)
REDIS_SSE_DB = config("REDIS_SSE_DB", cast=int, default=5)

# ----------------------------------------------
# REDIS
#

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": f"redis://redis:6379/{REDIS_CACHE_DB}",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

# ----------------------------------------------
# FLOWER
#
FLOWER_URL = config("FLOWER_URL", default="http://localhost:5555")
FLOWER_URL_PREFIX = "flower"
