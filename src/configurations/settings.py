# Copyright (C) 2024 BIRU
#
# This file is part of Tenzu.
#
# Tenzu is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# You can contact BIRU at ask@biru.sh
"""
Django settings for configurations project.

Generated by 'django-admin startproject' using Django 4.2.3.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path

import sentry_sdk
from corsheaders.defaults import default_headers

from .conf import settings

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = settings.SECRET_KEY

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = settings.DEBUG

ALLOWED_HOSTS = ["*"]
# Remove the last slash generated by the pydactic AnyHttp
CSRF_TRUSTED_ORIGINS = [
    str(settings.BACKEND_URL).rstrip("/"),
    str(settings.FRONTEND_URL).rstrip("/"),
    *[str(cors).rstrip("/") for cors in settings.EXTRA_CORS],
]
CORS_ALLOWED_ORIGINS = [
    str(settings.BACKEND_URL).rstrip("/"),
    str(settings.FRONTEND_URL).rstrip("/"),
    *[str(cors).rstrip("/") for cors in settings.EXTRA_CORS],
]
CORS_ALLOW_HEADERS = (*default_headers, "correlation-id")


# Application definition

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # tenzu
    "base.db",
    "commons.storage",
    "emails",
    "mediafiles",
    "notifications",
    "projects.invitations",
    "projects.memberships",
    "projects.projects",
    "projects.roles",
    "stories.assignments",
    "stories.stories",
    "attachments",
    "comments",
    "tokens",
    "users",
    "workflows",
    "workspaces.invitations",
    "workspaces.memberships",
    "workspaces.workspaces",
    # 3-party
    "easy_thumbnails",
    "ninja_jwt.token_blacklist",
    "procrastinate.contrib.django",
    "corsheaders",
    "django_extensions",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "events.middlewares.AsyncCorrelationIdMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "configurations.urls"

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

WSGI_APPLICATION = "configurations.wsgi.application"

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": settings.DB_NAME,
        "USER": settings.DB_USER,
        "PASSWORD": settings.DB_PASSWORD,
        "HOST": settings.DB_HOST,
        "PORT": settings.DB_PORT,
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# https://docs.djangoproject.com/en/5.1/topics/auth/passwords/#using-argon2-with-django
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_ROOT = settings.STATIC_ROOT
STATIC_URL = settings.STATIC_URL

# Media files
# https://docs.djangoproject.com/en/4.0/topics/files/#file-storage

MEDIA_ROOT = settings.MEDIA_ROOT
MEDIA_URL = settings.MEDIA_URL

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

ASGI_APPLICATION = "configurations.asgi.application"

AUTH_USER_MODEL = "users.User"

NINJA_JWT = {
    # env timedelta assumes value is an integer in seconds
    "ACCESS_TOKEN_LIFETIME": 432000,  # dev: 5 days, prod: 5min
    "REFRESH_TOKEN_LIFETIME": 864000,  # dev: 10 days, prod: 4h
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS512",
    "SIGNING_KEY": "azerazerazerazerzaer",
    "UPDATE_LAST_LOGIN": False,
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
    "JWK_URL": None,
    "LEEWAY": 0,
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "username",
    "USER_AUTHENTICATION_RULE": "ninja_jwt.authentication.default_user_authentication_rule",
    "AUTH_TOKEN_CLASSES": ("ninja_jwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "ninja_jwt.models.TokenUser",
    "JTI_CLAIM": "jti",
}

# EMAIL

# common email settings
EMAIL_BACKEND = settings.EMAIL.EMAIL_BACKEND
DEFAULT_FROM_EMAIL = settings.EMAIL.DEFAULT_FROM_EMAIL

# smtp backend settings
EMAIL_HOST = settings.EMAIL.EMAIL_HOST
EMAIL_PORT = settings.EMAIL.EMAIL_PORT
EMAIL_HOST_USER = settings.EMAIL.EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = settings.EMAIL.EMAIL_HOST_PASSWORD
EMAIL_USE_TLS = settings.EMAIL.EMAIL_USE_TLS
EMAIL_USE_SSL = settings.EMAIL.EMAIL_USE_SSL
EMAIL_TIMEOUT = settings.EMAIL.EMAIL_TIMEOUT
EMAIL_SSL_CERTFILE = settings.EMAIL.EMAIL_SSL_CERTFILE
EMAIL_SSL_KEYFILE = settings.EMAIL.EMAIL_SSL_KEYFILE

# file backend settings
EMAIL_FILE_PATH = BASE_DIR / settings.EMAIL.EMAIL_FILE_PATH

###############################################################################
# 3-PARTY LIBS
###############################################################################


# easy_thumbnails

THUMBNAIL_ALIASES = {"": settings.IMAGES.THUMBNAIL_ALIASES}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": f"{settings.EVENTS.PUBSUB_BACKEND.value}",
        "CONFIG": {
            "hosts": [
                {
                    "address": f"redis://default:{settings.EVENTS.REDIS_PASSWORD}@{settings.EVENTS.REDIS_HOST}:{settings.EVENTS.REDIS_PORT}/{settings.EVENTS.REDIS_DATABASE}",
                    **settings.EVENTS.REDIS_OPTIONS,
                }
            ],
        },
    },
}

LOG_FORMAT = "[{levelname}] <{asctime}> {pathname}:{lineno} {message}"
LOGLEVEL = "WARNING"
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "formatters": {
        "verbose": {
            "format": LOG_FORMAT,
            "style": "{",
        },
    },
    "loggers": {
        # root logger, for third party and such
        "": {
            "level": LOGLEVEL,
            "handlers": [
                "console",
            ],
        },
        "django": {
            "level": LOGLEVEL,
            "handlers": ["console"],
            # required to avoid double logging with root logger
            "propagate": False,
        },
    },
}

# Django integration is automatically enabled
# sentry-sdk will search for a SENTRY_DSN env variable and use it if set
# if it is empty or does not exist, no data will be sent
sentry_sdk.init(
    auto_session_tracking=False,
    traces_sample_rate=1.0,
)
