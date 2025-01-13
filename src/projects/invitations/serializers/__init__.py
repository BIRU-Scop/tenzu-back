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
from uuid import UUID

from pydantic import ConfigDict, EmailStr, validator

from base.serializers import BaseModel
from projects.invitations.choices import ProjectInvitationStatus
from projects.projects.serializers.nested import ProjectSmallNestedSerializer
from projects.roles.serializers.nested import ProjectRoleNestedSerializer
from users.serializers.nested import UserNestedSerializer


class PublicProjectInvitationSerializer(BaseModel):
    status: ProjectInvitationStatus
    email: EmailStr
    existing_user: bool
    available_logins: list[str]
    project: ProjectSmallNestedSerializer
    model_config = ConfigDict(from_attributes=True)


class ProjectInvitationSerializer(BaseModel):
    id: UUID
    project: ProjectSmallNestedSerializer
    user: UserNestedSerializer | None = None
    role: ProjectRoleNestedSerializer
    email: EmailStr
    workspace_id: UUID

    @staticmethod
    def resolve_workspace_id(obj):
        return obj.project.workspace_id

    model_config = ConfigDict(from_attributes=True)


class PrivateEmailProjectInvitationSerializer(BaseModel):
    id: UUID
    user: UserNestedSerializer | None = None
    role: ProjectRoleNestedSerializer
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


class CreateProjectInvitationsSerializer(BaseModel):
    invitations: list[PrivateEmailProjectInvitationSerializer]
    already_members: int
    model_config = ConfigDict(from_attributes=True)
