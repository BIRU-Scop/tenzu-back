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
from pydantic import EmailStr, Field, StrictBool, StringConstraints, field_validator
from typing_extensions import Annotated, Optional

from base.validators import BaseModel, LanguageCode
from users.api.validators.mixins import PasswordMixin

#####################################################################
# User
#####################################################################


class CreateUserValidator(PasswordMixin, BaseModel):
    email: EmailStr
    full_name: Annotated[str, StringConstraints(max_length=50)]  # type: ignore
    accept_terms: StrictBool
    color: Annotated[int, Field(gt=0, lt=9)] | None = None  # type: ignore
    lang: LanguageCode | None = None
    project_invitation_token: str | None = None
    workspace_invitation_token: str | None = None
    accept_project_invitation: StrictBool = True
    accept_workspace_invitation: StrictBool = True

    @field_validator("email", "full_name")
    @classmethod
    def check_not_empty(cls, v: str) -> str:
        assert v != "", "Empty field is not allowed"
        return v

    @field_validator("email")
    @classmethod
    def check_email_in_domain(cls, v: str) -> str:
        if not settings.USER_EMAIL_ALLOWED_DOMAINS:
            return v

        domain = v.split("@")[1]
        assert domain in settings.USER_EMAIL_ALLOWED_DOMAINS, "Email domain not allowed"
        return v

    @field_validator("accept_terms")
    @classmethod
    def check_accept_terms(cls, v: bool) -> bool:
        assert v is True, "User has to accept terms of service"
        return v


class UpdateUserValidator(BaseModel):
    full_name: Optional[Annotated[str, StringConstraints(max_length=50)]] = None
    lang: Optional[LanguageCode] = None
    password: Optional[str] = None

    @field_validator("full_name", "lang")
    @classmethod
    def check_not_empty(cls, v: str) -> str:
        assert v != "", "Empty field is not allowed"
        return v


class VerifyTokenValidator(BaseModel):
    token: str


#####################################################################
# Reset Password
#####################################################################


class RequestResetPasswordValidator(BaseModel):
    email: EmailStr


class ResetPasswordValidator(PasswordMixin, BaseModel):
    pass
