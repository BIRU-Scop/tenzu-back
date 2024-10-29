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
from typing import Final

from base.utils.enum import OrderedEnum


class TextDirection(str, Enum):
    RTL = "rtl"
    LTR = "ltr"


class ScriptType(str, OrderedEnum):
    LATIN = "latin"
    CYRILLIC = "cyrillic"
    GREEK = "greek"
    HEBREW = "hebrew"
    ARABIC = "arabic"
    CHINESE_AND_DEVS = "chinese_and_devs"
    OTHER = "other"


LATIN_LANGS: Final[list[str]] = [
    "ca",
    "da",
    "de",
    "en",
    "es",
    "eu",
    "fi",
    "gl",
    "fr",
    "it",
    "lv",
    "nb",
    "nl",
    "pl",
    "pt",
    "sv",
    "tr",
    "vi",
]

CYRILLIC_LANGS: Final[list[str]] = [
    "bg",
    "bs",
    "uk",
    "sr",
    "ru",
]
GREEK_LANGS: Final[list[str]] = [
    "el",
]
HEBREW_LANGS: Final[list[str]] = [
    "he",
]
ARABIC_LANGS: Final[list[str]] = [
    "fa",
    "ar",
]
CHINESE_AND_DEV_LANGS: Final[list[str]] = [
    "ko",
    "zh",
    "ja",
]


def get_script_type(identifier: str) -> ScriptType:
    if identifier in LATIN_LANGS:
        return ScriptType.LATIN
    if identifier in CYRILLIC_LANGS:
        return ScriptType.CYRILLIC
    if identifier in GREEK_LANGS:
        return ScriptType.GREEK
    if identifier in HEBREW_LANGS:
        return ScriptType.HEBREW
    if identifier in ARABIC_LANGS:
        return ScriptType.ARABIC
    if identifier in CHINESE_AND_DEV_LANGS:
        return ScriptType.CHINESE_AND_DEVS
    return ScriptType.OTHER
