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

import pytest
from asgiref.sync import sync_to_async

from configurations.api import api
from ninja_jwt.exceptions import AuthenticationFailed, InvalidToken
from ninja_jwt.tokens import AccessToken
from tests.utils import factories as f

pytestmark = [pytest.mark.django_db]


async def test_authenticate_success_without_token(async_rf):
    request = async_rf.get("/")
    for auth in api.auth:
        user = await auth(request)

        assert user is None


async def test_authenticate_success_with_token(async_rf):
    user = await f.create_user()
    token = await sync_to_async(AccessToken.for_user)(user)

    request = async_rf.get("/", headers={"Authorization": f"Bearer {token}"})

    for auth in api.auth:
        user = await auth(request)

        assert not user.is_anonymous
        assert user == user


async def test_authenticate_error_invalid_token(async_rf):
    request = async_rf.get("/", headers={"Authorization": "Bearer invalid-token"})

    for auth in api.auth:
        with pytest.raises(InvalidToken):
            await auth(request)


async def test_authenticate_error_invalid_user(async_rf):
    user = await f.create_user(is_active=False)
    token = await sync_to_async(AccessToken.for_user)(user)

    request = async_rf.get("/", headers={"Authorization": f"Bearer {token}"})

    for auth in api.auth:
        with pytest.raises(AuthenticationFailed):
            await auth(request)

    await user.adelete()
    for auth in api.auth:
        with pytest.raises(AuthenticationFailed):
            await auth(request)
