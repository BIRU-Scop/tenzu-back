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
from django.core.serializers.json import DjangoJSONEncoder

from .conf import settings
from .utils import remove_ending_slash

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

locals().update(
    # don't use model_dumps to prevent conversion to dict of nested models
    {
        field_name: field_value
        for field_name, field_value in settings
        if field_name not in {"DB", "EXTRA_CORS", "TOKENS", "EMAIL", "EVENTS"}
    }
)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

ALLOWED_HOSTS = [settings.BACKEND_URL.host, settings.FRONTEND_URL.host]
POD_IP = settings.POD_IP
if POD_IP:
    ALLOWED_HOSTS.append(POD_IP)


CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS = [
    remove_ending_slash(str(settings.BACKEND_URL)),
    remove_ending_slash(str(settings.FRONTEND_URL)),
    *settings.EXTRA_CORS,
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
    "users",
    "workflows",
    "workspaces.invitations",
    "workspaces.memberships",
    "workspaces.workspaces",
    # 3-party
    "easy_thumbnails",
    "ninja_jwt",
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
        **settings.DB.model_dump(),
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

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

ASGI_APPLICATION = "configurations.asgi.application"

AUTH_USER_MODEL = "users.User"

NINJA_JWT = {
    # env timedelta assumes value is an integer in seconds
    **settings.TOKENS.model_dump(),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "VERIFYING_KEY": None,
    "JWK_URL": None,
    "LEEWAY": 0,
    "USER_AUTHENTICATION_RULE": "ninja_jwt.authentication.default_user_authentication_rule",
    "AUTH_TOKEN_CLASSES": ("ninja_jwt.tokens.AccessToken",),
    "TOKEN_USER_CLASS": "ninja_jwt.models.TokenUser",
    "JSON_ENCODER": DjangoJSONEncoder,
}

AUTHENTICATION_BACKENDS = ["auth.backends.EmailOrUsernameModelBackend"]

# EMAIL

locals().update(settings.EMAIL.model_dump(exclude={"EMAIL_FILE_PATH"}))

# file backend settings
EMAIL_FILE_PATH = BASE_DIR / settings.EMAIL.EMAIL_FILE_PATH

###############################################################################
# 3-PARTY LIBS
###############################################################################


# easy_thumbnails

THUMBNAIL_ALIASES = settings.IMAGES.THUMBNAIL_ALIASES

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
