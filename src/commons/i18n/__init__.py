# Copyright (C) 2026 BIRU
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

import functools
from dataclasses import dataclass

from django.utils import translation

from configurations.utils import BASE_DIR

TRANSLATION_DIRECTORY = BASE_DIR / "locale"


@dataclass
class Locale:
    code: str
    generic_lang_code: str
    name: str
    name_local: str
    name_translated: str
    bidi: bool


@functools.cache
def get_locales() -> list[Locale]:
    """
    List with all the available locales as `Locale` objects.

    :return a list with all the available locales
    :rtype list[Locale]
    """
    locales = []
    for p in TRANSLATION_DIRECTORY.glob("*"):
        if p.is_dir():
            language_code = translation.to_language(p.parts[-1])
            language_info = translation.get_language_info(language_code)
            language_info["code"] = language_code
            locales.append(
                Locale(**language_info, generic_lang_code=language_code.split("-")[0])
            )

    return locales


@functools.cache
def get_available_languages() -> set[str]:
    """
    List with the codes for all the available languages.

    :return a list of locale codes
    :rtype list[str]
    """
    return {loc.code for loc in get_locales()}
