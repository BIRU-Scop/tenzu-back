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
import datetime

from pydantic import ConfigDict, EmailStr, field_validator, validator
from pydantic_core.core_schema import ValidationInfo

from base.serializers import UUIDB64, BaseModel
from memberships.choices import InvitationStatus
from users.serializers.nested import UserNestedSerializer


class RoleSerializer(BaseModel):
    id: UUIDB64
    name: str
    slug: str
    is_owner: bool
    order: int
    editable: bool
    permissions: list[str]
    model_config = ConfigDict(from_attributes=True)


class InvitationBaseSerializer(BaseModel):
    id: UUIDB64
    status: InvitationStatus
    user: UserNestedSerializer | None = None
    role_id: UUIDB64
    email: EmailStr
    resent_at: datetime.datetime | None
    created_at: datetime.datetime


class _PrivateEmailInvitationSerializer(InvitationBaseSerializer):
    email: EmailStr | None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("email", mode="after")
    @classmethod
    def avoid_to_publish_email_if_user(cls, value: str, info: ValidationInfo) -> str:
        user = info.data.get("user")
        return None if user else value


class CreateInvitationsSerializer(BaseModel):
    invitations: list[_PrivateEmailInvitationSerializer]
    already_members: int
    model_config = ConfigDict(from_attributes=True)


class PublicPendingInvitationBaseSerializer(BaseModel):
    email: EmailStr
    existing_user: bool
    available_logins: list[str]
