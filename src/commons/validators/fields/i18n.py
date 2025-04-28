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

from typing import Annotated

from django.conf import settings
from pydantic import (
    AfterValidator,
)
from pydantic.json_schema import WithJsonSchema

from base.i18n import i18n


def language_available(v: str) -> str:
    if not i18n.is_language_available(v):
        raise ValueError(f"Language {v} is not available")
    return v


LanguageCode = Annotated[
    str,
    AfterValidator(language_available),
    WithJsonSchema(
        {"example": settings.LANGUAGE_CODE, "enum": i18n.available_languages}
    ),
]
