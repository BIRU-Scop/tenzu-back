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

from integrations.google import exceptions as ex
from integrations.google.auth import services
from integrations.google.services import GoogleUserProfile

##########################################################
# google_login
##########################################################


async def test_google_login_ok():
    settings.GOOGLE_CLIENT_ID = "id"
    settings.GOOGLE_CLIENT_SECRET = "secret"
    with (
        patch(
            "integrations.google.auth.services.google_services", autospec=True
        ) as fake_google_services,
        patch(
            "integrations.google.auth.services.integrations_auth_services",
            autospec=True,
        ) as fake_integrations_auth_services,
    ):
        fake_google_services.get_access_to_google.return_value = "access_token"
        fake_google_services.get_user_info_from_google.return_value = GoogleUserProfile(
            email="email@test.com", full_name="Full Name", google_id="1", bio="Bio"
        )
        await services.google_login(
            code="code", redirect_uri="https://redirect.uri", lang="es-ES"
        )
        fake_integrations_auth_services.social_login.assert_awaited_once()


async def test_google_login_google_not_configured():
    settings.GOOGLE_CLIENT_ID = None
    settings.GOOGLE_CLIENT_SECRET = None
    with pytest.raises(ex.GoogleLoginError):
        await services.google_login(code="code", redirect_uri="https://redirect.uri")


async def test_google_login_invalid_code():
    settings.GOOGLE_CLIENT_ID = "id"
    settings.GOOGLE_CLIENT_SECRET = "secret"
    with (
        patch(
            "integrations.google.auth.services.google_services", autospec=True
        ) as fake_google_services,
        pytest.raises(ex.GoogleLoginAuthenticationError),
    ):
        fake_google_services.get_access_to_google.return_value = None
        await services.google_login(code="code", redirect_uri="https://redirect.uri")


async def test_google_login_google_api_not_responding():
    settings.GITLAB_CLIENT_ID = "id"
    settings.GITLAB_CLIENT_SECRET = "secret"
    with (
        patch(
            "integrations.google.auth.services.google_services", autospec=True
        ) as fake_google_services,
        pytest.raises(ex.GoogleAPIError),
    ):
        fake_google_services.get_access_to_google.return_value = "access_token"
        fake_google_services.get_user_info_from_google.return_value = None
        await services.google_login(code="code", redirect_uri="https://redirect.uri")
