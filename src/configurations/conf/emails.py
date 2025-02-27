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

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from configurations.utils import BASE_DIR


class EmailBackends(StrEnum):
    SMTP = "django.core.mail.backends.smtp.EmailBackend"
    CONSOLE = "django.core.mail.backends.console.EmailBackend"
    FILE = "django.core.mail.backends.filebased.EmailBackend"
    LOC_MEM = "django.core.mail.backends.locmem.EmailBackend"
    DUMMY = "django.core.mail.backends.dummy.EmailBackend"
    CONSOLE_TEXT = "emails.backends.console_text.EmailBackend"


class EmailSettings(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    # common email settings
    EMAIL_BACKEND: EmailBackends = EmailBackends.FILE
    DEFAULT_FROM_EMAIL: EmailStr = Field(default="username@domain.name")

    # smtp backend settings
    EMAIL_HOST: str = "localhost"
    EMAIL_PORT: int = 25
    EMAIL_HOST_USER: str = ""
    EMAIL_HOST_PASSWORD: str = ""
    EMAIL_USE_TLS: bool = False
    EMAIL_USE_SSL: bool = False
    EMAIL_TIMEOUT: int | None = None
    # path to a PEM-formatted certificate chain file to use for the SSL connection
    EMAIL_SSL_CERTFILE: str | None = None
    # path to a PEM-formatted private key file to use for the SSL connection
    EMAIL_SSL_KEYFILE: str | None = None
    # send the SMTP Date header of email messages in the local time zone or in UTC
    EMAIL_USE_LOCALTIME: bool = False

    # file backend settings
    EMAIL_FILE_PATH: str = BASE_DIR / "file_emails"
