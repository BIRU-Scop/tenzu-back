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

from configurations.conf import settings


def test_overwrite_settings_in_sync_test(override_settings):
    old_secret = settings.SECRET_KEY
    new_secret = "test-secret"

    assert old_secret != new_secret

    with override_settings({"SECRET_KEY": new_secret}):
        assert settings.SECRET_KEY == new_secret

    assert settings.SECRET_KEY == old_secret


async def test_overwrite_settings_in_async_test(override_settings):
    old_secret = settings.SECRET_KEY
    new_secret = "test-secret"

    assert old_secret != new_secret

    assert settings.SECRET_KEY == old_secret

    with override_settings({"SECRET_KEY": new_secret}):
        assert settings.SECRET_KEY == new_secret

    assert settings.SECRET_KEY == old_secret


async def test_overwrite_settings_mutiples_times(override_settings):
    old_secret = settings.SECRET_KEY
    new_secret = "test-secret"
    old_url = settings.BACKEND_URL
    new_url = "http://test-overwrite-settings.com"

    assert old_secret != new_secret
    assert old_url != new_url

    assert settings.SECRET_KEY == old_secret
    assert settings.BACKEND_URL == old_url

    with override_settings({"SECRET_KEY": new_secret}):
        assert settings.SECRET_KEY == new_secret
        assert settings.BACKEND_URL == old_url

    assert settings.SECRET_KEY == old_secret
    assert settings.BACKEND_URL == old_url

    with override_settings({"BACKEND_URL": new_url}):
        assert settings.SECRET_KEY == old_secret
        assert settings.BACKEND_URL == new_url

    assert settings.SECRET_KEY == old_secret
    assert settings.BACKEND_URL == old_url
