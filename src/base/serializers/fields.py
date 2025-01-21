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

from typing import Annotated, Any, Callable, Generator
from uuid import UUID

from pydantic import AnyHttpUrl, BeforeValidator, PlainSerializer
from pydantic.json_schema import WithJsonSchema

from base.utils.strings import dict_to_camel
from base.utils.uuid import encode_uuid_to_b64str
from commons.utils import get_absolute_url

CallableGenerator = Generator[Callable[..., Any], None, None]

UUIDB64 = Annotated[
    UUID,
    PlainSerializer(encode_uuid_to_b64str, return_type=str),
    WithJsonSchema({"example": "6JgsbGyoEe2VExhWgGrI2w"}),
]


FileField = Annotated[
    AnyHttpUrl,
    BeforeValidator(get_absolute_url),
    PlainSerializer(str, return_type=str, when_used="unless-none"),
]


CamelizeDict = Annotated[
    dict,
    PlainSerializer(dict_to_camel, return_type=dict),
]
