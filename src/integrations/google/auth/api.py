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
from integrations.google.auth import services as auth_google_services
from integrations.google.auth.validators import GoogleLoginValidator
from ninja_jwt.schema import TokenObtainPairOutputSchema

google_integration_router = Router()


@google_integration_router.post(
    "/auth/google",
    url_name="auth.google",
    summary="Login / register with Google",
    response={
        200: TokenObtainPairOutputSchema,
        400: ERROR_RESPONSE_400,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
    auth=None,
)
async def google_login(
    request, form: GoogleLoginValidator
) -> TokenObtainPairOutputSchema:
    """
    Get an access and refresh token using a Google authorization.
    For a non-existing user, this process registers a new user as well.
    """
    return await auth_google_services.google_login(
        code=form.code, redirect_uri=form.redirect_uri, lang=form.lang
    )
