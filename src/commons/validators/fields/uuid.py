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

from typing import Annotated, Any
from uuid import UUID

from pydantic import BeforeValidator
from pydantic.json_schema import WithJsonSchema
from pydantic_core import PydanticCustomError

from base.utils.uuid import decode_b64str_to_uuid


def _decode_b64str_to_uuid(value: Any) -> UUID:
    if isinstance(value, UUID):
        return value
    if not isinstance(value, str):
        raise PydanticCustomError("string_type", "Input should be a valid string")
    return decode_b64str_to_uuid(value)


B64UUID = Annotated[
    UUID,
    BeforeValidator(_decode_b64str_to_uuid),
    WithJsonSchema({"example": "6JgsbGyoEe2VExhWgGrI2w"}),
]
