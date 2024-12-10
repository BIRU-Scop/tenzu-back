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

"""
Email backend that writes text messages to console instead of sending them.
"""

from typing import Protocol

from django.core.mail.backends.console import (
    EmailBackend as BaseEmailBackend,  # type: ignore[import]
)


class Message(Protocol):
    from_email: str
    to: str
    subject: str
    body: str


class EmailBackend(BaseEmailBackend):
    def _write_separator(self, separator: str) -> None:
        self.stream.write(separator * 79)
        self.stream.write("\n")

    def write_message(self, message: Message) -> None:
        self._write_separator("=")
        self.stream.write("FROM: %s, TO: %s\n" % (message.from_email, message.to))

        self._write_separator("-")
        self.stream.write("SUBJECT: %s\n" % message.subject)

        self._write_separator("-")
        self.stream.write("%s\n" % message.body)

        self._write_separator("=")
