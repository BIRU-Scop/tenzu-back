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

from typing import Any, Callable, Generator, Type

from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, core_schema

from base.i18n import i18n
from configurations.conf import settings

CallableGenerator = Generator[Callable[..., Any], None, None]


class LanguageCode(str):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_after_validator_function(cls, handler(str))

    @classmethod
    # TODO[pydantic]: We couldn't refactor `__modify_schema__`,
    #  please create the `__get_pydantic_json_schema__` manually.
    # Check https://docs.pydantic.dev/latest/migration/#defining-custom-types for more information.
    def __get_pydantic_json_schema__(
        cls, cs: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        json_schema = handler(cs)
        json_schema = handler.resolve_ref_schema(json_schema)
        json_schema.update(
            type="string",
            example=settings.LANG,
            enum=i18n.available_languages,
        )
        return json_schema

    @classmethod
    # TODO[pydantic]: We couldn't refactor `__get_validators__`,
    #  please create the `__get_pydantic_core_schema__` manually.
    # Check https://docs.pydantic.dev/latest/migration/#defining-custom-types for more information.
    def __get_validators__(cls: Type["LanguageCode"]) -> CallableGenerator:
        yield cls.validate

    @classmethod
    def validate(cls: Type["LanguageCode"], value: str) -> str:
        assert i18n.is_language_available(value), "Language is not available"
        return value
