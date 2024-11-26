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

from dataclasses import dataclass
from typing import Final

import httpx
from django.conf import settings

HEADERS: Final[dict[str, str]] = {
    "Accept": "application/json",
}
ACCESS_TOKEN_URL: Final[str] = "https://oauth2.googleapis.com/token"
USER_API_URL: Final[str] = "https://openidconnect.googleapis.com/v1/userinfo"


@dataclass
class GoogleUserProfile:
    google_id: str
    email: str
    full_name: str
    bio: str


async def get_access_to_google(code: str, redirect_uri: str) -> str | None:
    headers = HEADERS.copy()
    headers["Content-Type"] = "application/x-www-form-urlencoded"

    params = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }

    async with httpx.AsyncClient() as async_client:
        response = await async_client.post(
            ACCESS_TOKEN_URL,
            headers=headers,
            data=params,
            auth=(settings.GOOGLE_CLIENT_ID, settings.GOOGLE_CLIENT_SECRET),  # type: ignore
        )

    data = response.json()
    if response.status_code != 200 or "error" in data:
        return None

    return data.get("access_token", None)


async def get_user_info_from_google(access_token: str) -> GoogleUserProfile | None:
    headers = HEADERS.copy()
    headers["Authorization"] = f"Bearer {access_token}"

    async with httpx.AsyncClient() as async_client:
        response_user = await async_client.get(USER_API_URL, headers=headers)

    if response_user.status_code != 200:
        return None

    user_profile = response_user.json()

    return GoogleUserProfile(
        email=user_profile.get("email"),
        google_id=user_profile.get("sub"),
        full_name=user_profile.get("name"),
        bio=user_profile.get("hd"),
    )
