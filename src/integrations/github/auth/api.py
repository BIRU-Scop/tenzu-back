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

from ninja import Router

from commons.exceptions.api.errors import ERROR_RESPONSE_400, ERROR_RESPONSE_422
from integrations.github.auth import services as auth_github_services
from integrations.github.auth.validators import GithubLoginValidator
from ninja_jwt.schema import TokenObtainPairOutputSchema

github_integration_router = Router()


@github_integration_router.post(
    "/auth/github",
    url_name="auth.github",
    summary="Login / register with Github",
    response={
        200: TokenObtainPairOutputSchema,
        400: ERROR_RESPONSE_400,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
    auth=None,
)
async def github_login(
    request, form: GithubLoginValidator
) -> TokenObtainPairOutputSchema:
    """
    Get an access and refresh token using a Github authorization.
    For a non-existing user, this process registers a new user as well.
    """
    return await auth_github_services.github_login(code=form.code, lang=form.lang)
