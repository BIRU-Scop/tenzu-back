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
from datetime import timedelta

from pydantic import BaseModel, Field

from ninja_jwt.backends import AllowedAlgorithmsType


class TokensSettings(BaseModel):
    SIGNING_KEY: str
    ALGORITHM: AllowedAlgorithmsType = "HS512"
    VERIFYING_KEY: str = ""
    AUDIENCE: str | None = None
    ISSUER: str | None = None
    ACCESS_TOKEN_LIFETIME: timedelta = timedelta(minutes=5)
    REFRESH_TOKEN_LIFETIME: timedelta = timedelta(hours=4)

    TOKEN_TYPE_CLAIM: str = "token_type"
    JTI_CLAIM: str = "jti"
    USER_ID_FIELD: str = "id"
    USER_ID_CLAIM: str = "user_id"


class AccountSettings(BaseModel):
    SOCIALACCOUNT_REQUESTS_TIMEOUT: int = 5
    SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT: bool = True
    SOCIALACCOUNT_PROVIDERS: dict[str, dict] = Field(
        default_factory=dict
    )  # you can also use the admin app to dynamically add SocialApp instead, see https://docs.allauth.org/en/latest/socialaccount/provider_configuration.html
    SOCIALAPPS_PROVIDERS: list[str] = Field(default_factory=list)
