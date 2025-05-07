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

import functools
import operator

from django.conf import settings

from base.i18n import i18n
from system.serializers import (
    LanguageSerializer,
    ScriptType,
    TextDirection,
    get_script_type,
)


@functools.lru_cache
def get_available_languages_info() -> list[LanguageSerializer]:
    """
    List with the info for all the available languages.

    The languages order will be as follow:

    - First for the writing system (alphabet or script type) in this order: Latin, Cyrillic, Greek, Hebrew, Arabic,
      Chinese and derivatives, and others.
    - Second alphabetically for its language name.

    :return a list of `LanguageSchema` objects
    :rtype list[tenzu.base.i18n.schemas.LanguageSchema]
    """

    langs: list[LanguageSerializer] = []
    for loc in i18n.locales:
        code = i18n.get_locale_code(loc)
        script_type = get_script_type(loc.language)
        name = (
            loc.display_name.title()
            if loc.display_name and script_type is ScriptType.LATIN
            else loc.display_name or code
        )
        english_name = loc.english_name or code
        text_direction = TextDirection(loc.text_direction)
        is_default = code == settings.LANGUAGE_CODE

        langs.append(
            LanguageSerializer(
                code=code,
                name=name,
                english_name=english_name,
                text_direction=text_direction,
                is_default=is_default,
                script_type=script_type,
            )
        )

    langs.sort(key=operator.attrgetter("script_type", "name"))
    return langs
