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

from unittest.mock import patch

import pytest
from django.conf import settings

from integrations.github import exceptions as ex
from integrations.github.auth import services
from integrations.github.services import GithubUserProfile

##########################################################
# github_login
##########################################################


async def test_github_login_ok():
    settings.GITHUB_CLIENT_ID = "id"
    settings.GITHUB_CLIENT_SECRET = "secret"
    with (
        patch(
            "integrations.github.auth.services.github_services", autospec=True
        ) as fake_github_services,
        patch(
            "integrations.github.auth.services.integrations_auth_services",
            autospec=True,
        ) as fake_integrations_auth_services,
    ):
        fake_github_services.get_access_to_github.return_value = "access_token"
        fake_github_services.get_user_info_from_github.return_value = GithubUserProfile(
            email="email@test.com", full_name="Full Name", github_id="1", bio="Bio"
        )
        await services.github_login(code="code", lang="es-ES")
        fake_integrations_auth_services.social_login.assert_awaited_once()


async def test_github_login_github_not_configured():
    settings.GITHUB_CLIENT_ID = None
    settings.GITHUB_CLIENT_SECRET = None
    with pytest.raises(ex.GithubLoginError):
        await services.github_login(code="code")


async def test_github_login_invalid_code():
    settings.GITHUB_CLIENT_ID = "id"
    settings.GITHUB_CLIENT_SECRET = "secret"
    with (
        patch(
            "integrations.github.auth.services.github_services", autospec=True
        ) as fake_github_services,
        pytest.raises(ex.GithubLoginAuthenticationError),
    ):
        fake_github_services.get_access_to_github.return_value = None
        await services.github_login(code="invalid-code")


async def test_github_login_github_api_not_responding():
    settings.GITHUB_CLIENT_ID = "id"
    settings.GITHUB_CLIENT_SECRET = "secret"
    with (
        patch(
            "integrations.github.auth.services.github_services", autospec=True
        ) as fake_github_services,
        pytest.raises(ex.GithubAPIError),
    ):
        fake_github_services.get_access_to_github.return_value = "access_token"
        fake_github_services.get_user_info_from_github.return_value = None
        await services.github_login(code="code")
