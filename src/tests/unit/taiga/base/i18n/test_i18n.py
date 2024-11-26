# -*- coding: utf-8 -*-
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

from unittest.mock import PropertyMock, patch

import pytest

from base import templating
from base.i18n import FALLBACK_LOCALE, I18N, Locale, UnknownLocaleIdentifierError


def test_i18n_is_created_with_the_falback_lang():
    i18n = I18N()
    assert i18n.translations.info()["language"] == str(FALLBACK_LOCALE)
    assert len(i18n._translations_cache) == 1


def test_i18n_is_initialized_with_the_config_lang(
    override_settings, initialize_template_env
):
    settings_lang = "es-ES"
    with override_settings({"LANGUAGE_CODE": settings_lang}), initialize_template_env():
        i18n = I18N()

        orig_trans = i18n.translations
        assert orig_trans.info()["language"] == str(FALLBACK_LOCALE)
        assert (
            "jinja2.ext.InternationalizationExtension" not in templating.env.extensions
        )
        assert "gettext" not in templating.env.globals
        assert len(i18n._translations_cache) == 1

        i18n.initialize()

        init_trans = i18n.translations
        assert init_trans.info()["language"] == settings_lang.replace("-", "_")
        assert "jinja2.ext.InternationalizationExtension" in templating.env.extensions
        assert templating.env.globals["gettext"] == init_trans.gettext
        assert len(i18n._translations_cache) == 2  # fallback != settings lang


def test_i18n_set_lang(override_settings, initialize_template_env):
    settings_lang = "en-US"
    lang = "es-ES"
    with override_settings({"LANGUAGE_CODE": settings_lang}), initialize_template_env():
        i18n = I18N()
        i18n.initialize()

        init_trans = i18n.translations
        assert init_trans.info()["language"] == settings_lang.replace("-", "_")
        assert "jinja2.ext.InternationalizationExtension" in templating.env.extensions
        assert templating.env.globals["gettext"] == init_trans.gettext
        assert len(i18n._translations_cache) == 1  # fallback == settings lang

        i18n.set_lang(lang)

        new_trans = i18n.translations
        assert new_trans.info()["language"] == lang.replace("-", "_")
        assert "jinja2.ext.InternationalizationExtension" in templating.env.extensions
        assert templating.env.globals["gettext"] == new_trans.gettext
        assert len(i18n._translations_cache) == 2


def test_i18n_set_lang_with_invalid_identifier(
    override_settings, initialize_template_env
):
    settings_lang = "en-US"
    invalid_lang = "invalid"

    with override_settings({"LANGUAGE_CODE": settings_lang}), initialize_template_env():
        i18n = I18N()
        i18n.initialize()

        init_trans = i18n.translations
        assert init_trans.info()["language"] == settings_lang.replace("-", "_")
        assert "jinja2.ext.InternationalizationExtension" in templating.env.extensions
        assert templating.env.globals["gettext"] == init_trans.gettext
        assert len(i18n._translations_cache) == 1  # fallback == settings lang

        with pytest.raises(UnknownLocaleIdentifierError):
            i18n.set_lang(invalid_lang)

        new_trans = i18n.translations
        assert new_trans.info()["language"] == settings_lang.replace("-", "_")
        assert "jinja2.ext.InternationalizationExtension" in templating.env.extensions
        assert templating.env.globals["gettext"] == new_trans.gettext
        assert len(i18n._translations_cache) == 1


def test_i18n_reset_lang(override_settings):
    settings_lang = "es-ES"
    lang = "en-US"
    with override_settings({"LANGUAGE_CODE": settings_lang}):
        i18n = I18N()
        i18n.initialize()
        i18n.set_lang(lang)

        assert i18n.translations.info()["language"] == lang.replace("-", "_")

        i18n.reset_lang()

        assert i18n.translations.info()["language"] == settings_lang.replace("-", "_")


def test_i18n_use_contextmanager(override_settings):
    settings_lang = "es-ES"
    lang = "en-US"
    with override_settings({"LANGUAGE_CODE": settings_lang}):
        i18n = I18N()
        i18n.initialize()

        assert i18n.translations.info()["language"] == settings_lang.replace("-", "_")

        with i18n.use(lang):
            assert i18n.translations.info()["language"] == lang.replace("-", "_")

        assert i18n.translations.info()["language"] == settings_lang.replace("-", "_")


@pytest.mark.parametrize(
    "lang, result",
    [
        ("en_US", False),
        ("en-US", True),
        ("invalid_lang", False),
    ],
)
def test_i18n_if_is_language_available(lang, result):
    i18n = I18N()
    assert i18n.is_language_available(lang) == result


def test_i19n_get_available_languages_info_return_sorted_list():
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

        i18n = I18N()
        assert sorted_codes == [lang.code for lang in i18n.available_languages_info]
