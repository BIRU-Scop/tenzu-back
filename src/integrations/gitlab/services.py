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

from dataclasses import dataclass
from typing import Final

import httpx
from django.conf import settings

HEADERS: Final[dict[str, str]] = {
    "Accept": "application/json",
}


@dataclass
class GitlabUserProfile:
    gitlab_id: str
    email: str
    full_name: str
    bio: str


async def get_access_to_gitlab(code: str, redirect_uri: str) -> str | None:
    ACCESS_TOKEN_URL: Final[str] = f"{settings.GITLAB_URL}/oauth/token"

    headers = HEADERS.copy()
    params = {
        "code": code,
        "client_id": settings.GITLAB_CLIENT_ID,
        "client_secret": settings.GITLAB_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }

    async with httpx.AsyncClient() as async_client:
        response = await async_client.post(
            ACCESS_TOKEN_URL, params=params, headers=headers
        )

    data = response.data
    if response.status_code != 200 or "error" in data:
        return None

    return data.get("access_token", None)


async def get_user_info_from_gitlab(access_token: str) -> GitlabUserProfile | None:
    USER_API_URL: Final[str] = f"{settings.GITLAB_URL}/api/v4/user"

    headers = HEADERS.copy()
    headers["Authorization"] = f"Bearer {access_token}"

    async with httpx.AsyncClient() as async_client:
        response_user = await async_client.get(USER_API_URL, headers=headers)

    if response_user.status_code != 200:
        return None

    user_profile = response_user.json()
    full_name = user_profile.get("name") or user_profile.get("username")

    return GitlabUserProfile(
        email=user_profile.get("email"),
        gitlab_id=user_profile.get("id"),
        full_name=full_name,
        bio=user_profile.get("bio"),
    )
