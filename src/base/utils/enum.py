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

import functools
from enum import Enum
from typing import Any


@functools.total_ordering
class OrderedEnum(Enum):
    """
    This class is the same as `enum.Enum` but the order of the attributes defined in the child classes will be used
    for sorting.

    .. testsetup::
        class Places(OrderedEnum):
            city = "city"
            state = "state"
            country = "country"

    .. doctest::
        >>> Place.state < Place.country
        True
        >>> Place.state < Place.city
        False
        >>> Place.state == Place.state
        True
    """

    @classmethod
    @functools.lru_cache(None)
    def __members_list__(cls) -> list["OrderedEnum"]:
        return list(cls)

    def __lt__(self, other: Any) -> bool:
        if self.__class__ is other.__class__:
            ml = self.__class__.__members_list__()
            return ml.index(self) < ml.index(other)
        return NotImplemented
