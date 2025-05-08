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

from unittest.mock import PropertyMock, patch

from base.i18n import Locale
from system import services as system_services


def test_get_available_languages_info_return_sorted_list():
    codes = [
        "ar",
        "bg",
        "ca",
        "en-US",
        "es-ES",
        "eu",
        "fa",
        "he",
        "ja",
        "ko",
        "pt",
        "pt-BR",
        "ru",
        "uk",
        "zh-Hans",
        "zh-Hant",
    ]
    sorted_codes = [
        "ca",
        "en-US",
        "es-ES",
        "eu",
        "pt",
        "pt-BR",
        "bg",
        "ru",
        "uk",
        "he",
        "ar",
        "fa",
        "zh-Hans",
        "zh-Hant",
        "ja",
        "ko",
    ]
    with patch("base.i18n.I18N.locales", new_callable=PropertyMock) as locales_mock:
        locales_mock.return_value = [Locale.parse(cod, sep="-") for cod in codes]
        system_services.get_available_languages_info.cache_clear()  # prevent lru_cache from provoking flaky test
        assert sorted_codes == [
            lang.code for lang in system_services.get_available_languages_info()
        ]
