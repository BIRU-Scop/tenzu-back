# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 BIRU
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

from unittest.mock import Mock, patch

import pytest

from auth import services as auth_serv
from auth.services import exceptions as ex
from ninja_jwt.tokens import AccessToken, RefreshToken
from tests.utils import factories as f
from tests.utils.bad_params import NOT_EXISTING_UUID
from users.models import User

##########################################################
# login
##########################################################


async def test_login_success():
    username = "test_user"
    password = "test_password"
    user = f.build_user(username=username, password=password, is_active=True)

    with (
        patch("auth.services.users_repositories", autospec=True) as fake_users_repo,
        patch("tokens.base.tokens_services", autospec=True) as fake_tokens_services,
    ):
        fake_tokens_services.token_is_denied.return_value = False
        fake_tokens_services.outstanding_token_exist.return_value = False

        fake_users_repo.get_user.return_value = user
        fake_users_repo.check_password.return_value = True

        data = await auth_serv.login(username=username, password=password)

        assert data.token
        assert data.refresh

        fake_users_repo.get_user.assert_awaited_once_with(
            filters={"username_or_email": username, "is_active": True}
        )
        fake_users_repo.check_password.assert_awaited_once_with(
            user=user, password=password
        )
        fake_users_repo.update_last_login.assert_awaited_once_with(user=user)


async def test_login_error_invalid_username():
    invalid_username = "invalid_username"
    password = "test_password"

    with patch("auth.services.users_repositories", autospec=True) as fake_users_repo:
        fake_users_repo.get_user.side_effect = User.DoesNotExist

        data = await auth_serv.login(username=invalid_username, password=password)

        assert not data

        fake_users_repo.get_user.assert_awaited_once_with(
            filters={"username_or_email": invalid_username, "is_active": True}
        )
        fake_users_repo.check_password.assert_not_awaited()
        fake_users_repo.update_last_login.assert_not_awaited()


async def test_login_error_invalid_password():
    username = "test_user"
    password = "test_password"
    invalid_password = "invalid_password"
    user = f.build_user(username=username, password=password, is_active=True)

    with patch("auth.services.users_repositories", autospec=True) as fake_users_repo:
        fake_users_repo.get_user.return_value = user
        fake_users_repo.check_password.return_value = False

        data = await auth_serv.login(username=username, password=invalid_password)

        assert not data

        fake_users_repo.get_user.assert_awaited_once_with(
            filters={"username_or_email": username, "is_active": True}
        )
        fake_users_repo.check_password.assert_awaited_once_with(
            user=user, password=invalid_password
        )
        fake_users_repo.update_last_login.assert_not_awaited()


##########################################################
# refresh
##########################################################


async def test_refresh_success():
    user = f.build_user(is_active=True)
    token = Mock()  # this is the code of the future refresh_token

    with patch("tokens.base.tokens_services", autospec=True) as fake_tokens_services:
        fake_tokens_services.token_is_denied.return_value = False
        fake_tokens_services.outstanding_token_exist.return_value = True
        fake_tokens_services.get_or_create_outstanding_token.return_value = (
            token,
            None,
        )

        refresh_token = RefreshToken.for_user(user)
        token.return_value = str(refresh_token)

        data = await auth_serv.refresh(token=str(refresh_token))

        assert data.token and data.token != str(refresh_token.access_token)
        assert data.refresh and data.refresh != str(refresh_token)

        fake_tokens_services.deny_token.assert_awaited_once_with(token=token)


async def test_refresh_error_invalid_token():
    data = await auth_serv.refresh(token="invalid_token")
    assert not data


##########################################################
# authenticate
##########################################################


async def test_authenticate_success():
    user = f.build_user(id=1, is_active=False)
    token = AccessToken.for_user(user)

    with patch("auth.services.users_repositories", autospec=True) as fake_users_repo:
        fake_users_repo.get_user.return_value = user

        data = await auth_serv.authenticate(token=str(token))

        assert data[0] == ["auth"]
        assert data[1] == user


async def test_authenticate_error_bad_auth_token():
    with pytest.raises(ex.BadAuthTokenError):
        await auth_serv.authenticate(token="bad_token")


async def test_authenticate_error_inactive_user():
    user = f.build_user(id=1, is_active=False)
    token = AccessToken.for_user(user)

    with patch("auth.services.users_repositories", autospec=True) as fake_users_repo:
        fake_users_repo.get_user.side_effect = User.DoesNotExist

        with pytest.raises(ex.UnauthorizedUserError):
            await auth_serv.authenticate(token=str(token))


##########################################################
# deny_refresh_token
##########################################################


async def test_deny_refresh_token_success():
    user1 = f.build_user(id=NOT_EXISTING_UUID, is_active=True)
    token = Mock()  # this is the code of the future refresh_token

    with patch("tokens.base.tokens_services", autospec=True) as fake_tokens_services:
        fake_tokens_services.token_is_denied.return_value = False
        fake_tokens_services.outstanding_token_exist.return_value = True
        fake_tokens_services.get_or_create_outstanding_token.return_value = (
            token,
            None,
        )

        refresh_token = RefreshToken.for_user(user1)
        token.return_value = str(refresh_token)

        await auth_serv.deny_refresh_token(user=user1, token=str(refresh_token))

        fake_tokens_services.deny_token.assert_awaited_once_with(token=token)


async def test_deny_refresh_token_error_bad_refresh_token():
    user1 = f.build_user(id=NOT_EXISTING_UUID, is_active=True)
    invalid_token = "invalid_token"

    with patch("tokens.base.tokens_services", autospec=True) as fake_tokens_services:
        with pytest.raises(ex.BadRefreshTokenError):
            await auth_serv.deny_refresh_token(user=user1, token=invalid_token)

        fake_tokens_services.deny_token.assert_not_awaited()


async def test_deny_refresh_token_error_unauthorized_user():
    user1 = f.build_user(id=NOT_EXISTING_UUID, is_active=True)
    user2 = f.build_user(id=NOT_EXISTING_UUID, is_active=True)

    with patch("tokens.base.tokens_services", autospec=True) as fake_tokens_services:
        fake_tokens_services.token_is_denied.return_value = False
        fake_tokens_services.outstanding_token_exist.return_value = True

        refresh_token = RefreshToken.for_user(user1)

        with pytest.raises(ex.UnauthorizedUserError):
            await auth_serv.deny_refresh_token(user=user2, token=str(refresh_token))

        fake_tokens_services.deny_token.assert_not_awaited()
