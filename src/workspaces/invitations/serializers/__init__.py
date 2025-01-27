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

from typing import Any

from pydantic import ConfigDict, EmailStr, validator

from base.serializers import UUIDB64, BaseModel
from users.serializers.nested import UserNestedSerializer
from workspaces.invitations.choices import WorkspaceInvitationStatus
from workspaces.workspaces.serializers.nested import WorkspaceSmallNestedSerializer


class PrivateEmailWorkspaceInvitationSerializer(BaseModel):
    id: UUIDB64
    user: UserNestedSerializer | None = None
    email: EmailStr | None = None
    model_config = ConfigDict(from_attributes=True)

    # TODO[pydantic]: We couldn't refactor the `validator`, please replace it by `field_validator` manually.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-validators for more information.
    @validator("email")
    def avoid_to_publish_email_if_user(
        cls, email: str, values: dict[str, Any]
    ) -> str | None:
        user = values.get("user")
        if user:
            return None
        else:
            return email


class CreateWorkspaceInvitationsSerializer(BaseModel):
    invitations: list[PrivateEmailWorkspaceInvitationSerializer]
    already_members: int
    model_config = ConfigDict(from_attributes=True)


class PublicWorkspaceInvitationSerializer(BaseModel):
    status: WorkspaceInvitationStatus

    email: EmailStr
    existing_user: bool
    available_logins: list[str]
    workspace: WorkspaceSmallNestedSerializer
    model_config = ConfigDict(from_attributes=True)


class WorkspaceInvitationSerializer(BaseModel):
    id: UUIDB64
    workspace: WorkspaceSmallNestedSerializer
    user: UserNestedSerializer | None = None
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)
