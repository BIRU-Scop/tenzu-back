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

import re
from typing import Final

import pytest
from django.conf import settings
from fastapi import status

pytestmark = pytest.mark.django_db()

##########################################################
# POST /auth/gitlab
##########################################################


async def test_gitlab_login(client, httpx_mock):
    settings.GITLAB_CLIENT_ID = "id"
    settings.GITLAB_CLIENT_SECRET = "secret"
    settings.GITLAB_URL = "https://gitlab.com"

    ACCESS_URL_REGEX: Final[str] = re.compile(f"{settings.GITLAB_URL}/oauth/token.*")
    USER_URL_REGEX: Final[str] = re.compile(f"{settings.GITLAB_URL}/api/v4/user.*")

    httpx_mock.add_response(
        url=ACCESS_URL_REGEX,
        method="POST",
        status_code=200,
        json={"access_token": "TOKEN"},
    )
    httpx_mock.add_response(
        url=USER_URL_REGEX,
        method="GET",
        status_code=200,
        json={
            "login": "username",
            "email": "me@email.com",
            "bio": "my bio",
            "name": "full name",
            "id": 1,
        },
    )

    data = {"code": "code", "redirect_uri": "https://redirect.uri", "lang": "es-ES"}
    response = client.post("/auth/gitlab", json=data)

    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json().keys() == {"access", "refresh"}


async def test_gitlab_login_not_configured(client, httpx_mock):
    settings.GITLAB_CLIENT_ID = None
    settings.GITLAB_CLIENT_SECRET = None
    settings.GITLAB_URL = None

    data = {"code": "code", "redirect_uri": "https://redirect.uri"}
    response = client.post("/auth/gitlab", json=data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.text


async def test_gitlab_login_incorrect_code(client, httpx_mock):
    settings.GITLAB_CLIENT_ID = "id"
    settings.GITLAB_CLIENT_SECRET = "secret"
    settings.GITLAB_URL = "https://gitlab.com"

    ACCESS_URL_REGEX: Final[str] = re.compile(f"{settings.GITLAB_URL}/oauth/token.*")

    httpx_mock.add_response(
        url=ACCESS_URL_REGEX, method="POST", status_code=400, json={"error": "ERROR"}
    )

    data = {"code": "code", "redirect_uri": "https://redirect.uri"}
    response = client.post("/auth/gitlab", json=data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.text


async def test_gitlab_login_api_not_working(client, httpx_mock):
    settings.GITLAB_CLIENT_ID = "id"
    settings.GITLAB_CLIENT_SECRET = "secret"
    settings.GITLAB_URL = "https://gitlab.com"

    ACCESS_URL_REGEX: Final[str] = re.compile(f"{settings.GITLAB_URL}/oauth/token.*")
    USER_URL_REGEX: Final[str] = re.compile(f"{settings.GITLAB_URL}/api/v4/user.*")

    httpx_mock.add_response(
        url=ACCESS_URL_REGEX,
        method="POST",
        status_code=200,
        json={"access_token": "TOKEN"},
    )
    httpx_mock.add_response(url=USER_URL_REGEX, method="GET", status_code=400, json=[])

    data = {"code": "code", "redirect_uri": "https://redirect.uri"}
    response = client.post("/auth/gitlab", json=data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.text
