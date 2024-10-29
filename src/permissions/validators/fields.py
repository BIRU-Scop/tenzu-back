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

from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler, PlainSerializer, TypeAdapter
from pydantic.json_schema import JsonSchemaValue, WithJsonSchema
from pydantic_core import core_schema as cs

from permissions import choices

CallableGenerator = Generator[Callable[..., Any], None, None]


def validate_permissions(value: list[str]):
    assert _permissions_are_valid(permissions=value), "One or more permissions are not valid. Maybe, there is a typo."
    assert _permissions_are_compatible(permissions=value), "Given permissions are incompatible"
    return value


Permissions = Annotated[
    list[str],
    PlainSerializer(validate_permissions, return_type=list[str]),
    WithJsonSchema({"example": ["view_story"]}),
]


#
# class Permissions(list[str]):
#     @classmethod
#     # TODO[pydantic]: We couldn't refactor `__modify_schema__`, please create the `__get_pydantic_json_schema__` manually.
#     # Check https://docs.pydantic.dev/latest/migration/#defining-custom-types for more information.
#     def __get_pydantic_json_schema__(
#         cls, core_schema: cs.CoreSchema, handler: GetJsonSchemaHandler
#     ) -> JsonSchemaValue:
#         json_schema = handler(core_schema)
#         json_schema = handler.resolve_ref_schema(json_schema)
#
#         json_schema["example"] = ["view_story"]
#         json_schema["format"] = None
#         return json_schema
#     @classmethod
#     # TODO[pydantic]: We couldn't refactor `__get_validators__`, please create the `__get_pydantic_core_schema__` manually.
#     # Check https://docs.pydantic.dev/latest/migration/#defining-custom-types for more information.
#     def __get_validators__(cls) -> CallableGenerator:
#         yield cls.validate
#
#     @classmethod
#     def validate(cls, value: list[str]) -> list[str]:
#         assert _permissions_are_valid(
#             permissions=value
#         ), "One or more permissions are not valid. Maybe, there is a typo."
#         assert _permissions_are_compatible(permissions=value), "Given permissions are incompatible"
#         return value


def _permissions_are_valid(permissions: list[str]) -> bool:
    return set.issubset(set(permissions), set(choices.ProjectPermissions))


def _permissions_are_compatible(permissions: list[str]) -> bool:
    # a user cannot edit a story if she has no view permission
    if "view_story" not in permissions and set.intersection(set(permissions), choices.EditStoryPermissions):
        return False

    # a user cannot have "comment_story" permissions if she has no "view_story" permission
    if "comment_story" in permissions and "view_story" not in permissions:
        return False

    return True
