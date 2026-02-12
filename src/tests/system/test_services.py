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

from unittest.mock import PropertyMock, patch

from django.utils import translation

from commons.i18n import Locale
from system import services as system_services


def test_get_available_languages_info_return_sorted_list():
    codes = [
        "ar",
        "bg",
        "ca",
        "en-us",
        "es-es",
        "fa",
        "he",
        "ja",
        "ko",
        "pt",
        "pt-br",
        "ru",
        "uk",
        "zh-hans",
        "zh-hant",
    ]
    sorted_codes = [
        "ca",
        "en-us",
        "es-es",
        "pt",
        "pt-br",
        "bg",
        "ru",
        "uk",
        "he",
        "ar",
        "fa",
        "ja",
        "zh-hans",
        "zh-hant",
        "ko",
    ]
    with patch("commons.i18n.get_locales") as locales_mock:
        locales_mock.return_value = [
            Locale(
                **translation.get_language_info(cod)
                | {"code": cod, "generic_lang_code": cod.split("-")[0]}
            )
            for cod in codes
        ]
        system_services.get_available_languages_info.cache_clear()  # prevent lru_cache from provoking flaky test
        assert sorted_codes == [
            lang.code for lang in system_services.get_available_languages_info()
        ]
