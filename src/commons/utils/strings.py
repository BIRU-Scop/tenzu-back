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
from typing import Mapping

from pydantic.alias_generators import to_camel, to_snake

from commons.utils.slug import generate_incremental_int_suffix


def to_kebab(msg: str) -> str:
    return to_snake(msg).replace("_", "-")


def dict_to_camel(value: Mapping | list | str):
    if isinstance(value, Mapping):
        return {to_camel(k): dict_to_camel(v) for k, v in value.items()}
    if isinstance(value, list):
        return [dict_to_camel(k) for k in value]
    return value


def orderby_to_snake(data: str):
    snake_data = to_snake(data)
    return f"-{snake_data[1:]}" if data.startswith("-") else snake_data


def get_unique_string_with_max_length(
    value: str, max_length: int, unique_values: set[str], prefix: str = ""
):
    """
    get a new string with max_length while being unique in the given list
    """
    new_value = value[:max_length]
    suffix_generator = generate_incremental_int_suffix()
    while new_value in unique_values:
        suffix = next(suffix_generator)
        new_value = value[: max_length - len(prefix) - len(suffix)]
        new_value = f"{prefix}{new_value}{suffix}"
    return new_value
