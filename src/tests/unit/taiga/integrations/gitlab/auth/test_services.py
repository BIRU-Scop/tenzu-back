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

from integrations.gitlab import exceptions as ex
from integrations.gitlab.auth import services
from integrations.gitlab.services import GitlabUserProfile

##########################################################
# gitlab_login
##########################################################


async def test_gitlab_login_ok():
    settings.GITLAB_CLIENT_ID = "id"
    settings.GITLAB_CLIENT_SECRET = "secret"
    settings.GITLAB_URL = "https://gitlab.com"
    with (
        patch(
            "integrations.gitlab.auth.services.gitlab_services", autospec=True
        ) as fake_gitlab_services,
        patch(
            "integrations.gitlab.auth.services.integrations_auth_services",
            autospec=True,
        ) as fake_integrations_auth_services,
    ):
        fake_gitlab_services.get_access_to_gitlab.return_value = "access_token"
        fake_gitlab_services.get_user_info_from_gitlab.return_value = GitlabUserProfile(
            email="email@test.com", full_name="Full Name", gitlab_id="1", bio="Bio"
        )
        await services.gitlab_login(
            code="code", redirect_uri="https://redirect.uri", lang="es-ES"
        )
        fake_integrations_auth_services.social_login.assert_awaited_once()


async def test_gitlab_login_gitlab_not_configured():
    settings.GITLAB_CLIENT_ID = None
    settings.GITLAB_CLIENT_SECRET = None
    settings.GITLAB_URL = None
    with pytest.raises(ex.GitlabLoginError):
        await services.gitlab_login(code="code", redirect_uri="https://redirect.uri")


async def test_gitlab_login_invalid_code():
    settings.GITLAB_CLIENT_ID = "id"
    settings.GITLAB_CLIENT_SECRET = "secret"
    settings.GITLAB_URL = "https://gitlab.com"
    with (
        patch(
            "integrations.gitlab.auth.services.gitlab_services", autospec=True
        ) as fake_gitlab_services,
        pytest.raises(ex.GitlabLoginAuthenticationError),
    ):
        fake_gitlab_services.get_access_to_gitlab.return_value = None
        await services.gitlab_login(code="code", redirect_uri="https://redirect.uri")


async def test_gitlab_login_gitlab_api_not_responding():
    settings.GITLAB_CLIENT_ID = "id"
    settings.GITLAB_CLIENT_SECRET = "secret"
    settings.GITLAB_URL = "https://gitlab.com"
    with (
        patch(
            "integrations.gitlab.auth.services.gitlab_services", autospec=True
        ) as fake_gitlab_services,
        pytest.raises(ex.GitlabAPIError),
    ):
        fake_gitlab_services.get_access_to_gitlab.return_value = "access_token"
        fake_gitlab_services.get_user_info_from_gitlab.return_value = None
        await services.gitlab_login(code="code", redirect_uri="https://redirect.uri")
