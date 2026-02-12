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

import typing
from typing import Type, cast

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from ninja import ModelSchema, Schema
from ninja.schema import DjangoGetter
from pydantic import ValidationInfo, model_validator

import ninja_jwt.exceptions as exceptions
from ninja_jwt.utils import token_error
from users.models import User

from .settings import api_settings
from .tokens import RefreshToken, SlidingToken, UntypedToken

if api_settings.BLACKLIST_AFTER_ROTATION:
    from .token_blacklist.models import BlacklistedToken

user_name_field = User.USERNAME_FIELD  # type: ignore


class AuthUserSchema(ModelSchema):
    class Meta:
        model = User
        fields = [user_name_field]


class InputSchemaMixin:
    @classmethod
    def get_response_schema(cls) -> Type[Schema]:
        raise NotImplementedError("Must implement `get_response_schema`")

    def to_response_schema(self):
        _schema_type = self.get_response_schema()
        return _schema_type(**self.model_dump())


class TokenInputSchemaMixin(InputSchemaMixin):
    _user: User | None = None

    _default_error_messages = {
        "no_active_account": _("No active account found with the given credentials")
    }

    def check_user_authentication_rule(self) -> None:
        if not api_settings.USER_AUTHENTICATION_RULE(self._user):
            raise exceptions.AuthenticationFailed(
                self._default_error_messages["no_active_account"]
            )

    @classmethod
    def validate_values(cls, values: dict) -> dict:
        if user_name_field not in values and "password" not in values:
            raise exceptions.ValidationError(
                {
                    user_name_field: f"{user_name_field} is required",
                    "password": "password is required",
                }
            )

        if not values.get(user_name_field):
            raise exceptions.ValidationError(
                {user_name_field: f"{user_name_field} is required"}
            )

        if not values.get("password"):
            raise exceptions.ValidationError({"password": "password is required"})
        return values

    def validate_user_from_credentials(
        self, request: HttpRequest, values: dict
    ) -> None:
        _user = authenticate(request, **values)
        self._user = _user

        if not (_user is not None and _user.is_active):
            raise exceptions.AuthenticationFailed(
                self._default_error_messages["no_active_account"]
            )

    @classmethod
    def get_token(cls, user: User) -> dict:
        raise NotImplementedError(
            "Must implement `get_token` method for `TokenObtainInputSchemaBase` subclasses"
        )


class TokenObtainInputSchemaBase(ModelSchema, TokenInputSchemaMixin):
    _token_data: dict | None = None

    class Meta:
        model = User
        fields = ["password", user_name_field]

    @model_validator(mode="before")
    @classmethod
    def validate_inputs(cls, data: DjangoGetter) -> DjangoGetter:
        cls.validate_values(data._obj)
        return data

    @model_validator(mode="after")
    def post_validate(self, info: ValidationInfo) -> typing.Self:
        """
        This is a post validate process which is common for any token generating schema.
        """
        self.validate_user_from_credentials(
            request=info.context.get("request"), values=self.dict()
        )

        # get_token can return values that wants to apply to `OutputSchema`
        data = self.get_token(self._user)

        if not isinstance(data, dict):
            raise Exception("`get_token` must return a `dict` type.")

        self._token_data = data

        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, self._user)

        return self

    def get_response_schema_init_kwargs(self) -> dict:
        return dict(self.dict(exclude={"password"}), **self._token_data)

    def to_response_schema(self):
        _schema_type = self.get_response_schema()
        return _schema_type(**self.get_response_schema_init_kwargs())


class TokenObtainPairOutputSchema(AuthUserSchema):
    refresh: str
    access: str


class TokenObtainPairInputSchema(TokenObtainInputSchemaBase):
    @classmethod
    def get_response_schema(cls) -> Type[Schema]:
        return TokenObtainPairOutputSchema

    @classmethod
    def get_token(cls, user: User) -> dict:
        values = {}
        refresh = RefreshToken.for_user(user)
        refresh = cast(RefreshToken, refresh)
        values["refresh"] = str(refresh)
        values["access"] = str(refresh.access_token)
        return values


class TokenObtainSlidingOutputSchema(AuthUserSchema):
    token: str


class TokenObtainSlidingInputSchema(TokenObtainInputSchemaBase):
    @classmethod
    def get_response_schema(cls) -> Type:
        return TokenObtainSlidingOutputSchema

    @classmethod
    def get_token(cls, user: User) -> dict:
        values = {}
        slide_token = SlidingToken.for_user(user)
        values["token"] = str(slide_token)
        return values


class TokenRefreshInputSchema(Schema, InputSchemaMixin):
    refresh: str

    @model_validator(mode="before")
    @classmethod
    def validate_schema(cls, data: DjangoGetter) -> dict:
        data = data._obj

        if isinstance(data, dict):
            if not data.get("refresh"):
                raise exceptions.ValidationError({"refresh": "token is required"})
        return data

    @classmethod
    def get_response_schema(cls) -> Type[Schema]:
        return TokenRefreshOutputSchema


class TokenRefreshOutputSchema(Schema):
    refresh: str
    access: str

    @model_validator(mode="before")
    @classmethod
    @token_error
    def validate_schema(cls, data: DjangoGetter) -> typing.Any:
        data = data._obj

        if isinstance(data, dict):
            if not data.get("refresh"):
                raise exceptions.ValidationError(
                    {"refresh": "refresh token is required"}
                )

            refresh = RefreshToken(data["refresh"])

            new_data = {"access": str(refresh.access_token)}

            if api_settings.ROTATE_REFRESH_TOKENS:
                if api_settings.BLACKLIST_AFTER_ROTATION:
                    try:
                        # Attempt to blacklist the given refresh token
                        refresh.blacklist()
                    except AttributeError:
                        # If blacklist app not installed, `blacklist` method will
                        # not be present
                        pass

                refresh.set_jti()
                refresh.set_exp()
                refresh.set_iat()

                new_data["refresh"] = str(refresh)
            data.update(new_data)
        return data


class TokenRefreshSlidingInputSchema(Schema, InputSchemaMixin):
    token: str

    @model_validator(mode="before")
    @classmethod
    def validate_schema(cls, data: DjangoGetter) -> dict:
        data = data._obj
        if isinstance(data, dict):
            if not data.get("token"):
                raise exceptions.ValidationError({"token": "token is required"})
        return data

    @classmethod
    def get_response_schema(cls) -> Type[Schema]:
        return TokenRefreshSlidingOutputSchema


class TokenRefreshSlidingOutputSchema(Schema):
    token: str

    @model_validator(mode="before")
    @classmethod
    @token_error
    def validate_schema(cls, data: DjangoGetter) -> dict:
        data = data._obj

        if isinstance(data, dict):
            if not data.get("token"):
                raise exceptions.ValidationError({"token": "token is required"})

            token = SlidingToken(data["token"])

            # Check that the timestamp in the "refresh_exp" claim has not
            # passed
            token.check_exp(api_settings.SLIDING_TOKEN_REFRESH_EXP_CLAIM)

            # Update the "exp" and "iat" claims
            token.set_exp()
            token.set_iat()
            data.update({"token": str(token)})
        return data


class TokenVerifyInputSchema(Schema, InputSchemaMixin):
    token: str

    @model_validator(mode="before")
    @classmethod
    @token_error
    def validate_schema(cls, data: DjangoGetter) -> dict:
        data = data._obj

        if isinstance(data, dict):
            if not data.get("token"):
                raise exceptions.ValidationError({"token": "token is required"})
            token = UntypedToken(data["token"])

            if (
                api_settings.BLACKLIST_AFTER_ROTATION
                and "ninja_jwt.token_blacklist" in settings.INSTALLED_APPS
            ):
                jti = token.get(api_settings.JTI_CLAIM)
                if BlacklistedToken.objects.filter(token__jti=jti).exists():
                    raise exceptions.ValidationError("Token is blacklisted")

        return data

    @classmethod
    def get_response_schema(cls) -> Type[Schema]:
        return Schema

    def to_response_schema(self):
        return {}


class TokenBlacklistInputSchema(Schema, InputSchemaMixin):
    refresh: str

    @model_validator(mode="before")
    @classmethod
    @token_error
    def validate_schema(cls, data: DjangoGetter) -> dict:
        data = data._obj

        if isinstance(data, dict):
            if not (refresh_data := data.get("refresh")):
                raise exceptions.ValidationError(
                    {"refresh": "refresh token is required"}
                )
            refresh = RefreshToken(refresh_data)
            try:
                refresh.blacklist()
            except AttributeError:
                pass
        return data

    @classmethod
    def get_response_schema(cls) -> Type[Schema]:
        return Schema

    def to_response_schema(self):
        return {}
