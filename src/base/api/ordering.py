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

from fastapi.params import Query
from pydantic.alias_generators import to_camel, to_snake

from exceptions import api as ex

ORDER_DESC = """
List of fields to specify the ordering criteria. By default it will assume an ascending order, use the - sign
for a descending order.

Usage examples: `order=createdAt`, `order=createdAt&order=-text`
"""


class OrderQuery:
    _allowed: list[str] = []
    _default: list[str] = []

    def __init__(self, allowed: list[str], default: list[str]) -> None:
        self._allowed = allowed
        self._default = default

    def __call__(
        self, order: list[str] = Query([], description=ORDER_DESC)
    ) -> list[str]:  # type: ignore
        values: list[str] = list(map(to_snake, order)) if order else self._default  # type: ignore
        if invalids := set(values).difference(set(self._allowed)):
            raise ex.ValidationError(
                f"Invalid ordering fields: {', '.join(map(to_camel, invalids))}"
            )

        return values
