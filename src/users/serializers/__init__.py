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

from pydantic import ConfigDict, EmailStr

from base.serializers import UUIDB64, BaseModel
from ninja_jwt.schema import TokenObtainPairOutputSchema
from projects.invitations.serializers.nested import ProjectInvitationNestedSerializer
from projects.projects.serializers.mixins import ProjectLogoBaseSerializer
from projects.projects.serializers.nested import ProjectNestedSerializer
from workspaces.invitations.serializers.nested import (
    WorkspaceInvitationNestedSerializer,
)
from workspaces.workspaces.serializers.nested import WorkspaceSmallNestedSerializer


class UserBaseSerializer(BaseModel):
    username: str
    full_name: str
    color: int


class UserSerializer(UserBaseSerializer):
    email: EmailStr
    lang: str
    model_config = ConfigDict(from_attributes=True)


class UserSearchSerializer(UserBaseSerializer):
    user_is_member: bool | None = None
    user_has_pending_invitation: bool | None = None
    model_config = ConfigDict(from_attributes=True)


class VerificationInfoSerializer(BaseModel):
    auth: TokenObtainPairOutputSchema
    project_invitation: ProjectInvitationNestedSerializer | None = None
    workspace_invitation: WorkspaceInvitationNestedSerializer | None = None
    model_config = ConfigDict(from_attributes=True)


class _WorkspaceWithProjectsNestedSerializer(BaseModel):
    id: UUIDB64
    name: str
    slug: str
    color: int
    projects: list[ProjectNestedSerializer]
    model_config = ConfigDict(from_attributes=True)


class _ProjectWithWorkspaceNestedSerializer(ProjectLogoBaseSerializer):
    id: UUIDB64
    name: str
    slug: str
    description: str
    color: int
    workspace: WorkspaceSmallNestedSerializer
    model_config = ConfigDict(from_attributes=True)


class UserDeleteInfoSerializer(BaseModel):
    workspaces: list[_WorkspaceWithProjectsNestedSerializer]
    projects: list[_ProjectWithWorkspaceNestedSerializer]
    model_config = ConfigDict(from_attributes=True)
