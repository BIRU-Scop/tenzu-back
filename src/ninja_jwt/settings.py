# Copyright (C) 2024-2026 BIRU
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

# Copyright 2021 Ezeudoh Tochukwu
# https://github.com/eadwinCode/django-ninja-jwt
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from datetime import timedelta
from typing import Any, List, Optional, Self, Union

from django.conf import settings
from django.test.signals import setting_changed
from pydantic import (
    AnyUrl,
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from ninja_jwt.ninja_extra.lazy import LazyStrImport

NinjaJWT_SETTINGS_DEFAULTS = {
    "USER_AUTHENTICATION_RULE": "ninja_jwt.authentication.default_user_authentication_rule",
    "AUTH_TOKEN_CLASSES": ["ninja_jwt.tokens.AccessToken"],
    "TOKEN_USER_CLASS": "ninja_jwt.models.TokenUser",
}

USER_SETTINGS = getattr(
    settings,
    "SIMPLE_JWT",
    getattr(settings, "NINJA_JWT", NinjaJWT_SETTINGS_DEFAULTS),
)


class NinjaJWTSettings(BaseModel):
    ACCESS_TOKEN_LIFETIME: timedelta = Field(timedelta(minutes=5))
    REFRESH_TOKEN_LIFETIME: timedelta = Field(timedelta(days=1))
    ROTATE_REFRESH_TOKENS: bool = Field(False)
    BLACKLIST_AFTER_ROTATION: bool = Field(False)
    UPDATE_LAST_LOGIN: bool = Field(False)
    ALGORITHM: str = Field("HS256")
    SIGNING_KEY: str = Field(settings.SECRET_KEY)
    VERIFYING_KEY: Optional[str] = Field("")
    AUDIENCE: Optional[str] = Field(None)
    ISSUER: Optional[str] = Field(None)
    JWK_URL: Optional[AnyUrl] = Field(None)
    LEEWAY: Union[int, timedelta] = Field(0)

    # AUTH_HEADER_TYPES: Tuple[str] = Field(('Bearer',))
    # AUTH_HEADER_NAME: str = Field('HTTP_AUTHORIZATION')

    USER_ID_FIELD: str = Field("id")
    USER_ID_CLAIM: str = Field("user_id")

    USER_AUTHENTICATION_RULE: Any = Field(
        "ninja_jwt.authentication.default_user_authentication_rule"
    )
    TOKEN_USER_CLASS: Any = Field("ninja_jwt.models.TokenUser")
    AUTH_TOKEN_CLASSES: List[Any] = Field(["ninja_jwt.tokens.AccessToken"])
    JSON_ENCODER: Optional[Any] = Field(None)
    TOKEN_TYPE_CLAIM: Optional[str] = Field("token_type")
    JTI_CLAIM: Optional[str] = Field("jti")
    SLIDING_TOKEN_REFRESH_EXP_CLAIM: str = Field("refresh_exp")
    SLIDING_TOKEN_LIFETIME: timedelta = Field(timedelta(minutes=5))
    SLIDING_TOKEN_REFRESH_LIFETIME: timedelta = Field(timedelta(days=1))

    TOKEN_OBTAIN_PAIR_INPUT_SCHEMA: Any = Field(
        "ninja_jwt.schema.TokenObtainPairInputSchema"
    )
    TOKEN_OBTAIN_PAIR_REFRESH_INPUT_SCHEMA: Any = Field(
        "ninja_jwt.schema.TokenRefreshInputSchema"
    )

    TOKEN_OBTAIN_SLIDING_INPUT_SCHEMA: Any = Field(
        "ninja_jwt.schema.TokenObtainSlidingInputSchema"
    )
    TOKEN_OBTAIN_SLIDING_REFRESH_INPUT_SCHEMA: Any = Field(
        "ninja_jwt.schema.TokenRefreshSlidingInputSchema"
    )

    TOKEN_BLACKLIST_INPUT_SCHEMA: Any = Field(
        "ninja_jwt.schema.TokenBlacklistInputSchema"
    )
    TOKEN_VERIFY_INPUT_SCHEMA: Any = Field("ninja_jwt.schema.TokenVerifyInputSchema")

    @model_validator(mode="after")
    def validate_ninja_jwt_settings(self) -> Self:
        for item_key in NinjaJWT_SETTINGS_DEFAULTS.keys():
            item = getattr(self, item_key)
            if isinstance(item, (tuple, list)) and isinstance(item[0], str):
                setattr(self, item_key, [LazyStrImport(str(klass)) for klass in item])
            if isinstance(item, str):
                setattr(self, item_key, LazyStrImport(item))
        return self


# convert to lazy object
api_settings = NinjaJWTSettings(**USER_SETTINGS)


def reload_api_settings(*args: Any, **kwargs: Any) -> None:
    global api_settings

    setting, value = kwargs["setting"], kwargs["value"]

    if setting in ["SIMPLE_JWT", "NINJA_JWT"]:
        api_settings = NinjaJWTSettings(**value)


setting_changed.connect(reload_api_settings)
