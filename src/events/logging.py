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
import sys
from copy import copy
from typing import Any, Callable

from rich.style import Style

from base.logging.formatters import ColourizedFormatter


class EventsDefaultFormatter(ColourizedFormatter):
    action_colors: dict[str, Callable[[Any], str]] = {
        "register": lambda action: Style(action, color="green"),
        "unregister": lambda action: Style(action, color="magenta"),
        "subscribe": lambda action: Style(action, color="yellow"),
        "unsubscribe": lambda action: Style(action, color="blue"),
        "publish": lambda action: Style(action, color="bright_green"),
        "emit": lambda action: Style(action, color="bright_blue"),
        "default": lambda action: Style(action, color="white"),
    }

    def should_use_colors(self) -> bool:
        return sys.stderr.isatty()  # pragma: no cover

    def _color_action(self, action: str) -> str:
        def action_type(action: str) -> str:
            if action.endswith("unregister"):
                return "unregister"
            if action.endswith("register"):
                return "register"
            if action.endswith("unsubscribe"):
                return "unsubscribe"
            if action.endswith("subscribe"):
                return "subscribe"
            if action.endswith("publish"):
                return "publish"
            if action.endswith("emit"):
                return "emit"
            return "default"

        func = self.action_colors.get(
            action_type(action), self.action_colors["default"]
        )
        return func(action)

    def formatMessage(self, record: logging.LogRecord) -> str:
        recordcopy = copy(record)

        action = getattr(recordcopy, "action", "")
        action_seperator = " "

        if self.use_colors:
            action = self._color_action(action)

        recordcopy.__dict__["action"] = (
            f"[{Style('EV', bold=True, color='yellow')}: {action}]:{action_seperator}"
        )
        return super().formatMessage(recordcopy)


LOGGING_CONFIG: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "events.logging.EventsDefaultFormatter",
            "fmt": "%(levelprefix)s%(action)s%(message)s",
            "use_colors": None,
        },
    },
    "handlers": {
        "console": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    },
    "loggers": {
        "events": {"handlers": ["console"], "propagate": False, "level": "INFO"},
    },
}


def setup_logging(level: int = logging.INFO) -> None:
    copyconfig = copy(LOGGING_CONFIG)
    copyconfig["loggers"]["events"]["level"] = logging.getLevelName(level)
    logging.config.dictConfig(copyconfig)
