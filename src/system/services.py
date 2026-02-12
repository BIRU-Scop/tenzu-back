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

import functools
import operator

from django.conf import settings

from commons import i18n
from system.serializers import (
    LanguageSerializer,
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

    :return a list of `LanguageSerializer` objects
    :rtype list[system.serializers.LanguageSerializer]
    """

    langs: list[LanguageSerializer] = []
    for loc in i18n.get_locales():
        script_type = get_script_type(loc.generic_lang_code)
        is_default = loc.code == settings.LANGUAGE_CODE

        langs.append(
            LanguageSerializer(
                code=loc.code,
                name=loc.name_local,
                english_name=loc.name,
                text_direction=TextDirection.RTL if loc.bidi else TextDirection.LTR,
                is_default=is_default,
                script_type=script_type,
            )
        )

    langs.sort(key=lambda x: (x.script_type, x.name.title()))
    return langs
