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

from auth import services as auth_services
from base.utils import datetime
from base.utils.colors import generate_random_color
from configurations.conf import settings
from emails.emails import Emails
from emails.tasks import send_email
from ninja_jwt.schema import TokenObtainPairOutputSchema
from projects.invitations import services as project_invitations_services
from users import repositories as users_repositories
from users import services as users_services
from users.models import User
from workspaces.invitations import services as workspace_invitations_services


async def social_login(
    email: str,
    full_name: str,
    social_key: str,
    social_id: str,
    bio: str,
    lang: str | None = None,
) -> TokenObtainPairOutputSchema:
    user: User | None = None

    # check if the user exists and already has social login with the requested system
    auth_data = await users_repositories.get_auth_data(
        filters={"key": social_key, "value": social_id}
    )
    if auth_data:
        user = auth_data.user
    else:
        # check if the user exists (without social login yet)
        user = await users_repositories.get_user(filters={"email": email})
        lang = lang if lang else settings.LANG

        if not user:
            # create a new user with social login data and verify it
            color = generate_random_color()
            user = await users_repositories.create_user(
                email=email, full_name=full_name, password=None, lang=lang, color=color
            )
            await users_services.verify_user(user)
            await project_invitations_services.update_user_projects_invitations(
                user=user
            )
            await workspace_invitations_services.update_user_workspaces_invitations(
                user=user
            )
        elif not user.is_active:
            # update existing (but not verified) user with social login data and verify it
            # username and email are the same
            # but full_name is got from social login, and previous password is deleted
            user.full_name = full_name
            user.password = ""
            user.lang = lang
            user = await users_repositories.update_user(user=user)
            await users_services.verify_user(user)
            await project_invitations_services.update_user_projects_invitations(
                user=user
            )
            await workspace_invitations_services.update_user_workspaces_invitations(
                user=user
            )
        else:
            # the user existed and now is adding a new login method
            # so we send her a warning email
            await send_social_login_warning_email(
                full_name=user.full_name,
                email=user.email,
                login_method=social_key.capitalize(),
                lang=lang,
            )

        await users_repositories.create_auth_data(
            user=user, key=social_key, value=social_id
        )

    return await auth_services.create_auth_credentials(user=user)


async def send_social_login_warning_email(
    full_name: str, email: str, login_method: str, lang: str
) -> None:
    context = {
        "full_name": full_name,
        "login_method": login_method,
        "login_time": datetime.aware_utcnow(),
    }
    await send_email.defer(
        email_name=Emails.SOCIAL_LOGIN_WARNING.value,
        to=email,
        context=context,
        lang=lang,
    )
