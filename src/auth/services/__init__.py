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
from asgiref.sync import sync_to_async

from ninja_jwt import exceptions
from ninja_jwt.schema import TokenObtainPairInputSchema, TokenObtainPairOutputSchema
from ninja_jwt.settings import api_settings
from ninja_jwt.tokens import RefreshToken
from users import repositories as users_repositories
from users.models import User


async def create_auth_credentials(user: User) -> TokenObtainPairOutputSchema:
    """
    This function create new auth credentiasl (an access token and a refresh token) for one user.
    It will also update the date of the user's last login.
    """
    await users_repositories.update_last_login(user=user)
    if not api_settings.USER_AUTHENTICATION_RULE(user):
        raise exceptions.AuthenticationFailed(
            TokenObtainPairInputSchema._default_error_messages["no_active_account"]
        )

    refresh: RefreshToken = await sync_to_async(RefreshToken.for_user)(user)
    username_field = User.USERNAME_FIELD

    return TokenObtainPairOutputSchema(
        access=str(refresh.access_token),
        refresh=str(refresh),
        **{username_field: getattr(user, username_field)},
    )


async def get_available_user_logins(user: User) -> list[str]:
    available_social_user_logins = await users_repositories.list_auths_data(
        filters={"user_id": user.id}
    )
    available_user_logins = [x.key for x in available_social_user_logins]

    if user.password:
        available_user_logins.append("password")

    return available_user_logins
