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

import pytest
from fastapi import status

from configurations.conf import settings
from integrations.github import services

pytestmark = pytest.mark.django_db()

##########################################################
# POST /auth/github
##########################################################

ACCESS_URL_REGEX = re.compile(f"{services.ACCESS_TOKEN_URL}.*")
EMAILS_URL_REGEX = re.compile(f"{services.EMAILS_API_URL}.*")
USER_URL_REGEX = re.compile(f"{services.USER_API_URL}.*")


async def test_github_login(client, httpx_mock):
    settings.GITHUB_CLIENT_ID = "id"
    settings.GITHUB_CLIENT_SECRET = "secret"
    httpx_mock.add_response(
        url=ACCESS_URL_REGEX,
        method="POST",
        status_code=200,
        json={"access_token": "TOKEN"},
    )
    httpx_mock.add_response(
        url=EMAILS_URL_REGEX,
        method="GET",
        status_code=200,
        json=[
            {"email": "email1@email.com", "primary": False},
            {"email": "email2@email.com", "primary": True},
        ],
    )
    httpx_mock.add_response(
        url=USER_URL_REGEX,
        method="GET",
        status_code=200,
        json={
            "login": "username",
            "bio": "my bio",
            "name": "full name",
            "id": 1,
        },
    )

    data = {"code": "code", "lang": "es-ES"}
    response = client.post("/auth/github", json=data)

    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json().keys() == {"token", "refresh"}


async def test_github_login_not_configured(client, httpx_mock):
    settings.GITHUB_CLIENT_ID = None
    settings.GITHUB_CLIENT_SECRET = None

    data = {"code": "code"}
    response = client.post("/auth/github", json=data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.text


async def test_github_login_incorrect_code(client, httpx_mock):
    settings.GITHUB_CLIENT_ID = "id"
    settings.GITHUB_CLIENT_SECRET = "secret"
    httpx_mock.add_response(url=ACCESS_URL_REGEX, method="POST", status_code=400, json={"error": "ERROR"})

    data = {"code": "code"}
    response = client.post("/auth/github", json=data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.text


async def test_github_login_api_not_working(client, httpx_mock):
    settings.GITHUB_CLIENT_ID = "id"
    settings.GITHUB_CLIENT_SECRET = "secret"
    httpx_mock.add_response(
        url=ACCESS_URL_REGEX,
        method="POST",
        status_code=200,
        json={"access_token": "TOKEN"},
    )
    httpx_mock.add_response(url=EMAILS_URL_REGEX, method="GET", status_code=400, json=[])
    httpx_mock.add_response(url=USER_URL_REGEX, method="GET", status_code=400, json=[])

    data = {"code": "code"}
    response = client.post("/auth/github", json=data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.text
