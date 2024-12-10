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

from integrations.auth import services
from tests.utils import factories as f

##########################################################
# social_login
##########################################################


async def test_social_login_user_has_authdata():
    with (
        patch(
            "integrations.auth.services.users_repositories", autospec=True
        ) as fake_users_repositories,
        patch(
            "integrations.auth.services.auth_services", autospec=True
        ) as fake_auth_services,
    ):
        auth_data = f.build_auth_data()
        fake_users_repositories.get_auth_data.return_value = auth_data

        await services.social_login(
            email="", full_name="", social_key="", social_id="", bio=""
        )

        fake_auth_services.create_auth_credentials.assert_awaited_once()
        fake_users_repositories.get_user.assert_not_awaited()


async def test_social_login_user_no_auth_data():
    with (
        patch(
            "integrations.auth.services.users_repositories", autospec=True
        ) as fake_users_repositories,
        patch(
            "integrations.auth.services.auth_services", autospec=True
        ) as fake_auth_services,
    ):
        user = f.build_user()
        fake_users_repositories.get_auth_data.return_value = None
        fake_users_repositories.get_user.return_value = user

        await services.social_login(
            email="", full_name="", social_key="", social_id="", bio=""
        )

        fake_auth_services.create_auth_credentials.assert_awaited_once()
        fake_users_repositories.create_auth_data.assert_awaited_once()


async def test_social_login_no_user():
    with (
        patch(
            "integrations.auth.services.users_repositories", autospec=True
        ) as fake_users_repositories,
        patch(
            "integrations.auth.services.users_services", autospec=True
        ) as fake_users_services,
        patch(
            "integrations.auth.services.auth_services", autospec=True
        ) as fake_auth_services,
        patch(
            "integrations.auth.services.project_invitations_services", autospec=True
        ) as fake_pj_invitations_services,
        patch(
            "integrations.auth.services.workspace_invitations_services", autospec=True
        ) as fake_ws_invitations_services,
    ):
        fake_users_repositories.get_auth_data.return_value = None
        fake_users_repositories.get_user.return_value = None

        await services.social_login(
            email="", full_name="", social_key="", social_id="", bio=""
        )

        fake_users_repositories.create_user.assert_awaited_once()
        fake_users_services.verify_user.assert_awaited_once()
        fake_pj_invitations_services.update_user_projects_invitations.assert_awaited_once()
        fake_ws_invitations_services.update_user_workspaces_invitations.assert_awaited_once()
        fake_users_repositories.create_auth_data.assert_awaited_once()
        fake_auth_services.create_auth_credentials.assert_awaited_once()
