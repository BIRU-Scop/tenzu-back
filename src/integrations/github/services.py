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

from configurations.conf import settings

ACCESS_TOKEN_URL: Final[str] = "https://github.com/login/oauth/access_token"
EMAILS_API_URL: Final[str] = "https://api.github.com/user/emails"
USER_API_URL: Final[str] = "https://api.github.com/user"
HEADERS: Final[dict[str, str]] = {
    "Accept": "application/json",
}


@dataclass
class GithubUserProfile:
    github_id: str
    email: str
    full_name: str
    bio: str


async def get_access_to_github(code: str) -> str | None:
    headers = HEADERS.copy()
    params = {
        "code": code,
        "client_id": settings.GITHUB_CLIENT_ID,
        "client_secret": settings.GITHUB_CLIENT_SECRET,
        "scope": "user:emails",
    }
    async with httpx.AsyncClient() as async_client:
        response = await async_client.post(ACCESS_TOKEN_URL, params=params, headers=headers)

    data = response.json()
    if response.status_code != 200 or "error" in data:
        return None

    return data.get("access_token", None)


async def get_user_info_from_github(access_token: str) -> GithubUserProfile | None:
    headers = HEADERS.copy()
    headers["Authorization"] = f"token {access_token}"

    async with httpx.AsyncClient() as async_client:
        response_user = await async_client.get(USER_API_URL, headers=headers)
        response_emails = await async_client.get(EMAILS_API_URL, headers=headers)

    if response_user.status_code != 200 or response_emails.status_code != 200:
        return None

    user_profile = response_user.json()
    full_name = user_profile.get("name") or user_profile.get("login")

    emails = response_emails.json()
    primary_email = ""
    for e in emails:
        if e.get("primary"):
            primary_email = e["email"]
            break

    return GithubUserProfile(
        email=primary_email,
        github_id=user_profile.get("id"),
        full_name=full_name,
        bio=user_profile.get("bio"),
    )
