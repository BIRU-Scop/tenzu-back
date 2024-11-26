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

from django.conf import settings

from integrations.auth import services as integrations_auth_services
from integrations.github import exceptions as ex
from integrations.github import services as github_services
from ninja_jwt.schema import TokenObtainPairOutputSchema


async def github_login(
    code: str, lang: str | None = None
) -> TokenObtainPairOutputSchema:
    if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
        raise ex.GithubLoginError(
            "Login with Github is not available. Contact with the platform administrators."
        )

    access_token = await github_services.get_access_to_github(code=code)
    if not access_token:
        raise ex.GithubLoginAuthenticationError("The provided code is not valid.")

    user_info = await github_services.get_user_info_from_github(
        access_token=access_token
    )
    if not user_info:
        raise ex.GithubAPIError("Github API is not responding.")

    return await integrations_auth_services.social_login(
        email=user_info.email,
        full_name=user_info.full_name,
        social_key="github",
        social_id=user_info.github_id,
        bio=user_info.bio,
        lang=lang,
    )
