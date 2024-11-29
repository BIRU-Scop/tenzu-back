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
from fastapi import status

from auth.tokens import RefreshToken
from tests.utils import factories as f

pytestmark = pytest.mark.django_db


##########################################################
# auth/token
##########################################################


async def test_login_successfuly(client):
    password = "test_password"
    user = await f.create_user(password=password)

    data = {
        "username": user.username,
        "password": password,
    }

    response = client.post("/auth/token", json=data)
    assert response.status_code == 200, response.text
    assert response.json().keys() == {"access", "refresh"}


def test_login_error_invalid_credentials(client):
    data = {
        "username": "test_non_existing_user",
        "password": "test_password",
    }

    response = client.post("/auth/token", json=data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text
    assert response.headers["www-authenticate"] == 'Bearer realm="api"'


##########################################################
# auth/token/refresh
##########################################################


async def test_refresh_successfuly(client):
    user = await f.create_user(is_active=True)
    token = await RefreshToken.create_for_object(user)
    data = {
        "refresh": str(token),
    }

    response = client.post("/auth/token/refresh", json=data)
    assert response.status_code == 200, response.text
    assert response.json().keys() == {"access", "refresh"}


def test_refresh_error_invalid_token(client):
    data = {"refresh": "invalid_token"}

    response = client.post("/auth/token/refresh", json=data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text


##########################################################
# auth/token/deny
##########################################################


async def test_deny_refresh_token_success(client):
    user = await f.create_user()
    token = await RefreshToken.create_for_object(user)

    data = {
        "refresh": str(token),
    }

    client.login(user)
    response = client.post("/auth/blacklist", json=data)
    assert response.status_code == status.HTTP_204_NO_CONTENT, response.text


async def test_deny_refresh_token_error_bad_refresh_token(client):
    user = await f.create_user()

    data = {
        "refresh": "invalid_token",
    }

    client.login(user)
    response = client.post("/auth/blacklist", json=data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.text


async def test_deny_refresh_token_error_forbidden_user(client):
    user = await f.create_user()
    other_user = await f.create_user()
    token = await RefreshToken.create_for_object(user)

    data = {
        "refresh": str(token),
    }

    client.login(other_user)
    response = client.post("/auth/blacklist", json=data)
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text


async def test_deny_refresh_token_error_annonymous_user(client):
    user = await f.create_user()
    token = await RefreshToken.create_for_object(user)

    data = {
        "refresh": str(token),
    }

    response = client.post("/auth/blacklist", json=data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text
