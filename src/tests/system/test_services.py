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

from unittest.mock import patch

from base.i18n import I18N, Locale
from system import services as system_services
from tests.utils.utils import preserve_real_attrs


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
    locales_mock = [Locale.parse(cod, sep="-") for cod in codes]
    with patch("system.services.i18n", autospec=True) as fake_i18n:
        fake_i18n.locales = locales_mock
        preserve_real_attrs(
            fake_i18n,
            I18N,
            ["get_locale_code"],
        )
        assert sorted_codes == [
            lang.code for lang in system_services.get_available_languages_info()
        ]
