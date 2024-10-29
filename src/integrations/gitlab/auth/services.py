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

from configurations.conf import settings
from integrations.auth import services as integrations_auth_services
from integrations.gitlab import exceptions as ex
from integrations.gitlab import services as gitlab_services
from ninja_jwt.schema import TokenObtainPairOutputSchema


async def gitlab_login(code: str, redirect_uri: str, lang: str | None = None) -> TokenObtainPairOutputSchema:
    if not settings.GITLAB_CLIENT_ID or not settings.GITLAB_CLIENT_SECRET or not settings.GITLAB_URL:
        raise ex.GitlabLoginError("Login with Gitlab is not available. Contact with the platform administrators.")

    access_token = await gitlab_services.get_access_to_gitlab(code=code, redirect_uri=redirect_uri)
    if not access_token:
        raise ex.GitlabLoginAuthenticationError("The provided code is not valid.")

    user_info = await gitlab_services.get_user_info_from_gitlab(access_token=access_token)
    if not user_info:
        raise ex.GitlabAPIError("Gitlab API is not responding.")

    return await integrations_auth_services.social_login(
        email=user_info.email,
        full_name=user_info.full_name,
        social_key="gitlab",
        social_id=user_info.gitlab_id,
        bio=user_info.bio,
        lang=lang,
    )
