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

"""
This module is a wrapper of :py:mod: `babel.dates` to use the current selected locale to formatting date and time.

See the docs at `Babel - Date and Time <https://babel.pocoo.org/en/latest/api/dates.html>`_.
"""

from typing import Any, Callable

from babel import dates
from django.utils import translation


def _using_current_lang(func: Callable[..., Any]) -> Callable[..., Any]:
    def _wrapped_func(*args: Any, **kwargs: Any) -> Any:
        return func(*args, locale=translation.get_language(), **kwargs)

    return _wrapped_func


format_datetime = _using_current_lang(dates.format_datetime)
