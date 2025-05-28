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
from enum import Enum

from base.i18n import choices as i18n_choices
from base.serializers import BaseModel
from base.utils.enum import OrderedEnum


class TextDirection(Enum):
    RTL = "rtl"
    LTR = "ltr"


class ScriptType(OrderedEnum):
    LATIN = "latin"
    CYRILLIC = "cyrillic"
    GREEK = "greek"
    HEBREW = "hebrew"
    ARABIC = "arabic"
    CHINESE_AND_DEVS = "chinese_and_devs"
    OTHER = "other"


def get_script_type(identifier: str) -> ScriptType:
    if identifier in i18n_choices.LATIN_LANGS:
        return ScriptType.LATIN
    if identifier in i18n_choices.CYRILLIC_LANGS:
        return ScriptType.CYRILLIC
    if identifier in i18n_choices.GREEK_LANGS:
        return ScriptType.GREEK
    if identifier in i18n_choices.HEBREW_LANGS:
        return ScriptType.HEBREW
    if identifier in i18n_choices.ARABIC_LANGS:
        return ScriptType.ARABIC
    if identifier in i18n_choices.CHINESE_AND_DEV_LANGS:
        return ScriptType.CHINESE_AND_DEVS
    return ScriptType.OTHER


class LanguageSerializer(BaseModel):
    code: str
    name: str
    english_name: str
    script_type: ScriptType
    text_direction: TextDirection
    is_default: bool
