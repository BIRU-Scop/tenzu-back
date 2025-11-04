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


from typing import List, Self

from pydantic import (
    EmailStr,
    Field,
    field_validator,
    model_validator,
)
from typing_extensions import Annotated

from commons.validators import B64UUID, BaseModel
from users.api.validators import check_email_in_domain


class MembershipValidator(BaseModel):
    role_id: B64UUID


class DeleteMembershipQuery(BaseModel):
    successor_user_id: B64UUID | None = None


# --- Invitations


class _InvitationValidator(BaseModel):
    email: EmailStr | None = None
    username: str | None = None
    role_id: B64UUID

    @model_validator(mode="after")
    def username_or_email(self) -> Self:
        username_has_value = self.username is not None and self.username != ""
        email_has_value = self.email is not None and self.email != ""
        if not username_has_value and not email_has_value:
            raise ValueError("Username or email required")
        return self

    @field_validator("email")
    @classmethod
    def check_email_in_domain(cls, v: str | None) -> str | None:
        return check_email_in_domain(v)


class InvitationsValidator(BaseModel):
    # Max items 50 and duplicated items not allowed
    invitations: Annotated[List[_InvitationValidator], Field(max_length=50)]


class UpdateInvitationValidator(BaseModel):
    role_id: B64UUID
