# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 BIRU
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

import logging.config
from datetime import timedelta
from functools import lru_cache
from importlib import import_module
from pathlib import Path
from typing import Any

from pydantic import AnyHttpUrl, BaseModel, EmailStr, Field, field_validator
from pydantic_core.core_schema import ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict

from configurations.conf.emails import EmailSettings
from configurations.conf.events import EventsSettings
from configurations.conf.images import ImageSettings
from configurations.conf.logs import LOGGING_CONFIG
from configurations.conf.notifications import NotificationsSettings
from configurations.conf.storage import StorageSettings
from configurations.conf.tasksqueue import TaskQueueSettings
from configurations.conf.tokens import TokensSettings
from configurations.utils import remove_ending_slash

_DEFAULT_BACKEND_URL = AnyHttpUrl.build(scheme="http", host="localhost", port=8000)
_DEFAULT_FRONTEND_URL = AnyHttpUrl.build(scheme="http", host="localhost", port=4200)


class DbSettings(BaseModel):
    NAME: str = "tenzu"
    USER: str = "tenzu"
    PASSWORD: str = "tenzu"
    HOST: str = "localhost"
    PORT: int = 5432


class ExtraDep(BaseModel):
    app: str | None = None
    middleware: tuple[str, int] | tuple[None, None] = (None, None)
    auth: str | None = None
    api: str | None = None
    settings: dict[str, Any] = Field(default_factory=dict)
    settings_module: tuple[str, str] | tuple[None, None] = (None, None)


class Settings(BaseSettings):
    # Commons
    # SECURITY WARNING: keep the secret key used in production secret!
    SECRET_KEY: str
    SECRET_KEY_FALLBACKS: list[str] = Field(default_factory=list)
    UUID_NODE: int | None = None
    # SECURITY WARNING: don't run with debug turned on in production!
    DEBUG: bool = False

    # Kubernetes only
    POD_IP: str | None = None

    # Tenzu URLS
    BACKEND_URL: AnyHttpUrl = _DEFAULT_BACKEND_URL
    FRONTEND_URL: AnyHttpUrl = _DEFAULT_FRONTEND_URL
    EXTRA_CORS: list[AnyHttpUrl] = Field(default_factory=list)

    API_VERSION: str = "v1"

    EXTRA_DEPS: list[ExtraDep] = Field(default_factory=list)

    # Database
    DB: DbSettings = DbSettings()

    # Media and Static files
    # Static files (CSS, JavaScript, Images)
    # https://docs.djangoproject.com/en/4.0/howto/static-files/
    STATIC_URL: str = "/static/"
    STATIC_ROOT: Path = Path("/public/static")
    # Media files
    # https://docs.djangoproject.com/en/4.0/topics/files/#file-storage
    MEDIA_URL: str = "/media/"
    MEDIA_ROOT: Path = Path("/public/media")
    MAX_UPLOAD_FILE_SIZE: int = 100 * 1024 * 1024  # 100 MB

    # I18N
    LANGUAGE_CODE: str = "en-US"

    # Pagination
    DEFAULT_PAGE_SIZE: int = 10
    MAX_PAGE_SIZE: int = 100

    # Auth
    GITHUB_CLIENT_ID: str | None = None
    GITHUB_CLIENT_SECRET: str | None = None
    GITLAB_URL: str | None = None
    GITLAB_CLIENT_ID: str | None = None
    GITLAB_CLIENT_SECRET: str | None = None
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None

    # Users
    USER_EMAIL_ALLOWED_DOMAINS: list[str] = Field(default_factory=list)
    VERIFY_USER_TOKEN_LIFETIME: timedelta = timedelta(days=4)
    RESET_PASSWORD_TOKEN_LIFETIME: timedelta = timedelta(hours=2)

    # Workspaces & Projects
    GENERAL_INVITATION_LIFETIME: timedelta = timedelta(days=4)

    # Projects
    DEFAULT_PROJECT_TEMPLATE: str = "kanban"

    # Invitations
    INVITATION_RESEND_LIMIT: int = 100
    INVITATION_RESEND_TIME: int = 10  # 10 minutes

    # Workflows
    MAX_NUM_WORKFLOWS: int = 8

    # Tasks (linux crontab style)
    CLEAN_EXPIRED_USERS_CRON: str = "0 0 * * *"  # default: once a day
    CLEAN_EXPIRED_TOKENS_CRON: str = "0 0 * * *"  # default: once a day

    # Templates
    SUPPORT_EMAIL: EmailStr = Field(default="support@example.com")

    # Sub settings modules
    EMAIL: EmailSettings = EmailSettings()
    EVENTS: EventsSettings = EventsSettings()
    IMAGES: ImageSettings = ImageSettings()
    NOTIFICATIONS: NotificationsSettings = NotificationsSettings()
    STORAGE: StorageSettings = StorageSettings()
    TASKQUEUE: TaskQueueSettings = TaskQueueSettings()
    # can't be instantiated because it has one required value which will be set by environment
    TOKENS: TokensSettings

    # Remove the last slash generated by the pydantic AnyHttp
    @field_validator("EXTRA_CORS")
    @classmethod
    def set_extra_cors(cls, v: list[AnyHttpUrl], info: ValidationInfo) -> list[str]:
        return [remove_ending_slash(str(cors)) for cors in v]

    @field_validator("UUID_NODE")
    @classmethod
    def validate_uuid_node(cls, v: int | None) -> int | None:
        if v is not None and not 0 <= v < 1 << 48:
            raise ValueError("out of range (need a 48-bit value)")
        return v

    @field_validator("LANGUAGE_CODE")
    @classmethod
    def validate_lang(cls, v: str) -> str:
        from base.i18n import i18n

        if not i18n.is_language_available(v):
            available_languages_for_display = "\n".join(i18n.available_languages)
            raise ValueError(
                f"LANGUAGE_CODE should be one of \n{available_languages_for_display}\n"
            )
        return v

    model_config = SettingsConfigDict(
        env_prefix="TENZU_",
        env_nested_delimiter="__",
        case_sensitive=True,
        extra="allow",
    )


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    for extra_dep in settings.EXTRA_DEPS:
        module_name, module_path = extra_dep.settings_module
        if module_name is not None:
            extra_settings = import_module(module_path)
            setattr(settings, module_name, extra_settings.settings)
    return settings


logging.config.dictConfig(LOGGING_CONFIG)
settings: Settings = get_settings()
