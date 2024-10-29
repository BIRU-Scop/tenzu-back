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
from starlette.authentication import AuthenticationError as AuthorizationError

from auth import backend
from auth.tokens import AccessToken
from base.api import Request
from tests.utils import factories as f

pytestmark = [pytest.mark.django_db, pytest.mark.asyncio]

default_scope = {"type": "http", "headers": []}


async def test_authenticate_success_without_token():
    request = Request(default_scope)

    credential, user = await backend.authenticate(request)

    assert credential.scopes == []
    assert user.is_anonymous


async def test_authenticate_success_with_token():
    user = await f.create_user()
    token = await AccessToken.create_for_object(user)

    request = Request(default_scope)
    request._headers = {"Authorization": f"Bearer {token}"}

    credential, auth_user = await backend.authenticate(request)

    assert credential.scopes != []
    assert not auth_user.is_anonymous
    assert auth_user == user


async def test_authenticate_error_invalid_token():
    request = Request(default_scope)
    request._headers = {"Authorization": "Bearer invalid-token"}

    with pytest.raises(AuthorizationError):
        await backend.authenticate(request)
