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


import time
from datetime import timedelta

from base.i18n import ngettext


def timestamp_mics() -> int:
    """
    Return timestamp in microseconds.
    """
    return int(time.time() * 1000000)


def display_lifetime(lifetime: timedelta) -> str:
    """
    This function takes timedelta and return a string to round it to days, hours or minutes.
    If minutes are less than a day, then it returns hours.
    If minutes are less than an hour, then it returns the minutes.
    """
    if lifetime.days > 0:
        return (
            ngettext("datetime.lifetime.day", "datetime.lifetime.days", lifetime.days)
            % lifetime.days
        )
    else:
        hours, remainder = divmod(lifetime.seconds, 3600)
        if hours > 0:
            return (
                ngettext("datetime.lifetime.hour", "datetime.lifetime.hours", hours)
                % hours
            )
        else:
            minutes = remainder // 60
            return (
                ngettext(
                    "datetime.lifetime.minute", "datetime.lifetime.minutes", minutes
                )
                % minutes
            )
