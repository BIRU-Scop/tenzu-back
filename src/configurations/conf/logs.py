# -*- coding: utf-8 -*-
# Copyright (C) 2024-2026 BIRU
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
import logging
from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

LogLevel = Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"]
LogHandler = Literal["stream", "rich"]
LogKey = Literal[
    "root",
    "daphne",
    "django",
    "django.server",
    "django.db.backends",
    "django_auth_ldap",
    "channels",
    "events.consumers.event",
    "events.consumers.collaboration",
]

_DEFAULT_LOG_LEVELS: dict[LogKey, LogLevel] = {
    "root": "WARNING",
    "daphne": "WARNING",
    "django": "WARNING",
    "django.server": "INFO",
    "django.db.backends": "WARNING",
    "django_auth_ldap": "WARNING",
    "channels": "WARNING",
    "events.consumers.event": "WARNING",
    "events.consumers.collaboration": "WARNING",
}


def _merge_log_levels(v: Any) -> dict[LogKey, LogLevel]:
    defaults: dict[LogKey, LogLevel] = dict(_DEFAULT_LOG_LEVELS)
    if v is None:
        return defaults
    if not isinstance(v, dict):
        raise TypeError("LOG_LEVELS must be a dict")
    defaults.update(v)
    return defaults


LogLevels = Annotated[dict[LogKey, LogLevel], BeforeValidator(_merge_log_levels)]


class LogsSettings(BaseModel):
    model_config = ConfigDict(validate_default=True)
    LOG_LEVELS: LogLevels = Field(default_factory=dict)
    LOG_FORMAT_STREAM: str = "[{levelname}] <{asctime}> {pathname}:{lineno} {message}"
    LOG_FORMAT_RICH: str = "%(name)s: %(message)s"
    LOG_HANDLER: LogHandler = "rich"


LOGGER_COLORS = {
    "events.consumers.event": {
        "color": "cyan",
        "prefix": "EventConsumer",
    },
    "events.consumers.collaboration": {
        "color": "yellow",
        "prefix": "CollaborationConsumer",
    },
}


class RichLoggerColorFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        for prefix, color in LOGGER_COLORS.items():
            if record.name.startswith(prefix):
                record.msg = f"[{color['color']}][{color['prefix']}] {record.msg}[/{color['color']}]"
                break
        return True
