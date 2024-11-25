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

from humps.main import camelize
from pydantic import AnyHttpUrl, PlainSerializer
from pydantic.json_schema import WithJsonSchema

from base.utils.uuid import encode_uuid_to_b64str

CallableGenerator = Generator[Callable[..., Any], None, None]

UUIDB64 = Annotated[
    UUID,
    PlainSerializer(lambda x: encode_uuid_to_b64str(x), return_type=str),
    WithJsonSchema({"example": "6JgsbGyoEe2VExhWgGrI2w"}),
]

FileField = Annotated[
    AnyHttpUrl,
    PlainSerializer(lambda x: f"{x}", return_type=str),
]

CamelizeDict = Annotated[
    dict,
    PlainSerializer(lambda x: camelize(x).__str__(), return_type=str),
]

CamelizeDictJson = Annotated[
    dict,
    PlainSerializer(lambda x: camelize(x), return_type=str),
]
# class UUIDB64(UUID):
#     @classmethod
#     # Check https://docs.pydantic.dev/latest/migration/#defining-custom-types for more information.
#     def __get_pydantic_json_schema__(cls, core_schema: cs.CoreSchema, handler: GetJsonSchemaHandler) -> None:
#         json_schema = handler(core_schema)
#         json_schema = handler.resolve_ref_schema(json_schema)
#         json_schema['example'] = "6JgsbGyoEe2VExhWgGrI2w",
#         return json_schema
#
#     @classmethod
#     def __get_pydantic_core_schema__(
#         cls, source: Type[Any], handler: GetCoreSchemaHandler
#     ) -> core_schema.CoreSchema:
#         return core_schema.no_info_after_validator_function(
#             cls._validate,
#             core_schema.str_schema()
#         )
#     @classmethod
#     def _validate(cls, value: UUID) -> str:
#         return encode_uuid_to_b64str(value)


#
# class FileField(AnyHttpUrl):
#     @classmethod
#     def validate(cls, value: Any, field: Field, config: BaseConfig) -> AnyUrl:
#         return value.url


# _Key = TypeVar("_Key")
# _Val = TypeVar("_Val")
#
#
# class CamelizeDict(str):
#     @classmethod
#     def __get_pydantic_json_schema__(cls, core_schema: cs.CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
#         json_schema = handler(core_schema)
#         json_schema = handler.resolve_ref_schema(json_schema)
#         json_schema.update(
#             type="object",
#             example={},
#         )
#         return json_schema
#
#     @classmethod
#     def __get_pydantic_core_schema__(
#         cls, source: Type[Any], handler: GetCoreSchemaHandler
#     ) -> core_schema.CoreSchema:
#         return core_schema.no_info_after_validator_function(
#             cls.validate,
#             core_schema.str_schema()
#         )
#
#     @classmethod
#     def validate(cls, value: dict[_Key, _Val]) -> dict[_Key, _Val]:
#         return camelize(value)
#
#     def __repr__(self) -> str:
#         return "CamelizeDict"
