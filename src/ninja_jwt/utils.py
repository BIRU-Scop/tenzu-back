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

# Copyright 2021 Ezeudoh Tochukwu
# https://github.com/eadwinCode/django-ninja-jwt
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import logging
from calendar import timegm
from datetime import datetime
from functools import wraps
from importlib import import_module

from django.conf import settings
from django.utils.functional import lazy
from django.utils.timezone import is_naive, make_aware

from ninja_jwt import exceptions

try:
    from datetime import timezone
except ImportError:
    from django.utils import timezone


logger = logging.getLogger("django")


def token_error(func):
    @wraps(func)
    def _wrap(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except exceptions.TokenError as tex:
            raise exceptions.InvalidToken(str(tex)) from tex
        except Exception as ex:
            logger.error(f"{func} raised exception: {str(ex)}")
            raise ex

    return _wrap


def import_callable(path_or_callable):
    if callable(path_or_callable):
        return path_or_callable
    else:
        assert isinstance(path_or_callable, str)
        package, attr = path_or_callable.rsplit(".", 1)
        packages = import_module(package)
        return getattr(packages, attr)


def make_utc(dt):
    if settings.USE_TZ and is_naive(dt):
        return make_aware(dt, timezone=timezone.utc)

    return dt


def aware_utcnow():
    dt = datetime.now(tz=timezone.utc)
    if not settings.USE_TZ:
        dt = dt.replace(tzinfo=None)

    return dt


def datetime_to_epoch(dt):
    return timegm(dt.utctimetuple())


def datetime_from_epoch(ts):
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    if not settings.USE_TZ:
        dt = dt.replace(tzinfo=None)

    return dt


def format_lazy(s, *args, **kwargs):
    return s.format(*args, **kwargs)


format_lazy = lazy(format_lazy, str)
