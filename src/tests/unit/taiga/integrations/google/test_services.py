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

from integrations.google import services

ACCESS_URL_REGEX = re.compile(f"{services.ACCESS_TOKEN_URL}.*")
USER_URL_REGEX = re.compile(f"{services.USER_API_URL}.*")

##########################################################
# get_access_to_google
##########################################################


async def test_get_access_to_google_ok(httpx_mock):
    code = "code"
    redirect_uri = "https://redirect.uri"
    httpx_mock.add_response(
        url=ACCESS_URL_REGEX,
        method="POST",
        status_code=200,
        json={"access_token": "TOKEN"},
    )
    access_token = await services.get_access_to_google(code=code, redirect_uri=redirect_uri)
    assert access_token == "TOKEN"


async def test_get_access_to_google_ko(httpx_mock):
    code = "code"
    redirect_uri = "https://redirect.uri"
    httpx_mock.add_response(url=ACCESS_URL_REGEX, method="POST", status_code=400, json={"error": "ERROR"})
    access_token = await services.get_access_to_google(code=code, redirect_uri=redirect_uri)
    assert access_token is None


##########################################################
# get_user_info_from_google
##########################################################


async def test_get_user_info_from_google_ok(httpx_mock):
    access_token = "access_token"
    httpx_mock.add_response(
        url=USER_URL_REGEX,
        method="GET",
        status_code=200,
        json={"sub": "google_id", "email": "email", "name": "full name", "hd": "bio"},
    )
    user_profile = await services.get_user_info_from_google(access_token=access_token)
    assert user_profile.email == "email"
    assert user_profile.google_id == "google_id"
    assert user_profile.full_name == "full name"
    assert user_profile.bio == "bio"


async def test_get_user_info_from_google_users_api_wrong(httpx_mock):
    access_token = "access_token"
    httpx_mock.add_response(url=USER_URL_REGEX, method="GET", status_code=400, json={"error": "ERROR"})
    user_profile = await services.get_user_info_from_google(access_token=access_token)
    assert user_profile is None
