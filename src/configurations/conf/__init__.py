# -*- coding: utf-8 -*-
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

import logging.config
import os
import secrets
from functools import lru_cache
from pathlib import Path
from urllib.parse import urljoin

from pydantic import AnyHttpUrl, EmailStr, Field, field_validator, validator
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

_BASE_DIR = Path(__file__).resolve().parent.parent.parent  # is 'src'
_DEFAULT_BACKEND_URL = AnyHttpUrl.build(scheme="http", host="localhost", port=8000)
_DEFAULT_FRONTEND_URL = AnyHttpUrl.build(scheme="http", host="localhost", port=4200)
_DEFAULT_STATIC_URL = AnyHttpUrl.build(scheme="http", host="localhost", port=8000, path="/static/")
_DEFAULT_MEDIA_URL = AnyHttpUrl.build(scheme="http", host="localhost", port=8000, path="/media/")

class Settings(BaseSettings):
    # Commons
    SECRET_KEY: str = secrets.token_urlsafe(32)
    UUID_NODE: int | None = None
    DEBUG: bool = False

    # Tenzu URLS
    BACKEND_URL: AnyHttpUrl = _DEFAULT_BACKEND_URL
    FRONTEND_URL: AnyHttpUrl = _DEFAULT_FRONTEND_URL
    EXTRA_CORS: list[AnyHttpUrl] = []
    # Database
    DB_NAME: str = "tenzu"
    DB_USER: str = "tenzu"
    DB_PASSWORD: str = "tenzu"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432

    # Media and Static files
    STATIC_URL: AnyHttpUrl = _DEFAULT_STATIC_URL
    STATIC_ROOT: Path = _BASE_DIR.parent.joinpath("static/")
    MEDIA_URL: AnyHttpUrl = _DEFAULT_MEDIA_URL
    MEDIA_ROOT: Path = _BASE_DIR.parent.joinpath("media/")
    MAX_UPLOAD_FILE_SIZE: int = 100 * 1024 * 1024  # 100 MB

    # I18N
    LANG: str = "en-US"

    # Pagination
    DEFAULT_PAGE_SIZE: int = 10
    MAX_PAGE_SIZE: int = 100

    # Auth
    ACCESS_TOKEN_LIFETIME: int = 30  # 30 minutes
    REFRESH_TOKEN_LIFETIME: int = 8 * 24 * 60  # 8 * 24 * 60 minutes = 8 days
    GITHUB_CLIENT_ID: str | None = None
    GITHUB_CLIENT_SECRET: str | None = None
    GITLAB_URL: str | None = None
    GITLAB_CLIENT_ID: str | None = None
    GITLAB_CLIENT_SECRET: str | None = None
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None

    # Users
    USER_EMAIL_ALLOWED_DOMAINS: list[str] = []
    VERIFY_USER_TOKEN_LIFETIME: int = 4 * 24 * 60  # 4 * 24 * 60 minutes = 4 days
    RESET_PASSWORD_TOKEN_LIFETIME: int = 2 * 60  # 2 * 60 minutes = 2 hours

    # Workspaces
    WORKSPACE_INVITATION_LIFETIME: int = 4 * 24 * 60  # 4 * 24 * 60 minutes = 4 days

    # Projects
    DEFAULT_PROJECT_TEMPLATE: str = "kanban"

    # TODO: move this lifetime to general invitation lifetime for pj and ws
    PROJECT_INVITATION_LIFETIME: int = 4 * 24 * 60  # 4 * 24 * 60 minutes = 4 days

    # Invitations
    INVITATION_RESEND_LIMIT: int = 10
    INVITATION_RESEND_TIME: int = 10  # 10 minutes

    # Workflows
    MAX_NUM_WORKFLOWS: int = 8

    # Tasks (linux crontab style)
    CLEAN_EXPIRED_TOKENS_CRON: str = "0 0 * * *"  # default: once a day
    CLEAN_EXPIRED_USERS_CRON: str = "0 0 * * *"  # default: once a day

    # Templates
    SUPPORT_EMAIL: EmailStr = Field(default="support@example.com")

    # Sub settings modules
    EMAIL: EmailSettings = EmailSettings()
    EVENTS: EventsSettings = EventsSettings()
    IMAGES: ImageSettings = ImageSettings()
    NOTIFICATIONS: NotificationsSettings = NotificationsSettings()
    STORAGE: StorageSettings = StorageSettings()
    TASKQUEUE: TaskQueueSettings = TaskQueueSettings()
    TOKENS: TokensSettings = TokensSettings()

    @field_validator("UUID_NODE")
    @classmethod
    def validate_uuid_node(cls, v: int | None) -> int | None:
        if v is not None and not 0 <= v < 1 << 48:
            raise ValueError("out of range (need a 48-bit value)")
        return v

    @field_validator("STATIC_URL")
    @classmethod
    def set_static_url(cls, v: AnyHttpUrl, info: ValidationInfo) -> str:
        return v if v != _DEFAULT_STATIC_URL else urljoin(str(info.data["BACKEND_URL"]), "/static/")

    @field_validator("MEDIA_URL")
    @classmethod
    def set_media_url(cls, v: AnyHttpUrl, info: ValidationInfo) -> str:
        return v if v != _DEFAULT_MEDIA_URL else urljoin(str(info.data["BACKEND_URL"]), "/media/")

    @field_validator("LANG")
    @classmethod
    def validate_lang(cls, v: str) -> str:
        from base.i18n import i18n

        if not i18n.is_language_available(v):
            available_languages_for_display = "\n".join(i18n.available_languages)
            raise ValueError(f"LANG should be one of \n{ available_languages_for_display }\n")
        return v

    model_config = SettingsConfigDict(
        env_prefix="TENZU_",
        env_nested_delimiter="__",
        case_sensitive=True,
        env_file=os.getenv("TENZU_ENV_FILE", "caddy.env"),
        env_file_encoding=os.getenv("TENZU_ENV_FILE_ENCODING", "utf-8"),
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


logging.config.dictConfig(LOGGING_CONFIG)
settings: Settings = get_settings()
