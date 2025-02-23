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

#
#
# The code is partially taken (and modified) from djangorestframework-simplejwt v. 4.7.1
# (https://github.com/jazzband/djangorestframework-simplejwt/tree/5997c1aee8ad5182833d6b6759e44ff0a704edb4)
# that is licensed under the following terms:
#
#   Copyright 2017 David Sanders
#
#   Permission is hereby granted, free of charge, to any person obtaining a copy of
#   this software and associated documentation files (the "Software"), to deal in
#   the Software without restriction, including without limitation the rights to
#   use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
#   of the Software, and to permit persons to whom the Software is furnished to do
#   so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in all
#   copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#   SOFTWARE.

import time
from calendar import timegm
from datetime import datetime, timedelta, timezone
from datetime import time as datetime_time

from base.i18n import ngettext

_AnyTime = datetime | datetime_time


def is_aware(value: _AnyTime) -> bool:
    """
    Determines if a given datetime.datetime is aware.

    The concept is defined in Python's docs:
    http://docs.python.org/library/datetime.html#datetime.tzinfo

    Assuming value.tzinfo is either None or a proper datetime.tzinfo,
    value.utcoffset() implements the appropriate logic.
    """
    return value.utcoffset() is not None


def is_naive(value: _AnyTime) -> bool:
    """
    Determines if a given datetime.datetime is naive.

    The concept is defined in Python's docs:
    http://docs.python.org/library/datetime.html#datetime.tzinfo

    Assuming value.tzinfo is either None or a proper datetime.tzinfo,
    value.utcoffset() implements the appropriate logic.
    """
    return value.utcoffset() is None


def aware_utcnow() -> datetime:
    """
    Returns an aware datetime.utcnow()
    """
    return datetime.utcnow().replace(tzinfo=timezone.utc)


def datetime_to_epoch(dt: datetime) -> int:
    """
    Convert a datetime.datetime to its unix time representation.
    """
    return timegm(dt.utctimetuple())


def epoch_to_datetime(ts: int) -> datetime:
    """
    Convert a unix time representation to a datetime.datetime.
    """
    return datetime.fromtimestamp(ts, tz=timezone.utc)


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


def duration_iso_string(duration: timedelta) -> str:
    """
    Convert a timedelta objet to its ISO string representation.

    .. sourcecode:: python
        In: duration_iso_string(timedelta(days=2, seconds=4))
        Out: 'P2DT00H00M04S'

    Based on django code https://github.com/django/django/tree/stable/4.0.x/django/utils/duration.py#L31
    """

    def _get_duration_components(duration: timedelta) -> tuple[int, int, int, int, int]:
        days = duration.days
        seconds = duration.seconds
        microseconds = duration.microseconds

        minutes = seconds // 60
        seconds = seconds % 60

        hours = minutes // 60
        minutes = minutes % 60

        return days, hours, minutes, seconds, microseconds

    if duration < timedelta(0):
        sign = "-"
        duration *= -1
    else:
        sign = ""

    days, hours, minutes, seconds, microseconds = _get_duration_components(duration)
    ms = ".{:06d}".format(microseconds) if microseconds else ""
    return "{}P{}DT{:02d}H{:02d}M{:02d}{}S".format(
        sign, days, hours, minutes, seconds, ms
    )
