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


from typing import List, Self

from django.conf import settings
from pydantic import (
    EmailStr,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)
from pydantic_core.core_schema import ValidationInfo
from typing_extensions import Annotated

from commons.validators import BaseModel, check_not_empty


class MembershipValidator(BaseModel):
    role_slug: str

    @field_validator("role_slug")
    @classmethod
    def check_not_empty(cls, v: str) -> str:
        return check_not_empty(v)


# --- Invitations


class _InvitationValidator(BaseModel):
    email: EmailStr | None = None
    username: str | None = None
    role_slug: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=250)
    ]

    @model_validator(mode="after")
    def username_or_email(self) -> Self:
        username_has_value = self.username is not None and self.username != ""
        email_has_value = self.email is not None and self.email != ""
        if not username_has_value and not email_has_value:
            raise ValueError("Username or email required")
        return self

    @field_validator("email")
    @classmethod
    def check_email_in_domain(cls, v: str | None, info: ValidationInfo) -> str | None:
        if v is None or not settings.USER_EMAIL_ALLOWED_DOMAINS:
            return v

        domain = v.split("@")[1]
        if domain not in settings.USER_EMAIL_ALLOWED_DOMAINS:
            raise ValueError("Email domain not allowed")
        return v


class InvitationsValidator(BaseModel):
    # Max items 50 and duplicated items not allowed
    invitations: Annotated[List[_InvitationValidator], Field(max_length=50)]


class UpdateInvitationValidator(BaseModel):
    role_slug: str

    @field_validator("role_slug")
    @classmethod
    def check_not_empty(cls, v: str, info: ValidationInfo) -> str:
        return check_not_empty(v)
