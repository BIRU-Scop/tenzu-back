# -*- coding: utf-8 -*-
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
from pydantic import constr

from base.serializers import BaseModel
from ninja_jwt.schema import TokenObtainPairOutputSchema
from projects.invitations.serializers.nested import ProjectInvitationNestedSerializer
from projects.projects.serializers.nested import (
    ProjectLinkNestedSerializer,
    ProjectNestedSerializer,
)
from users.serializers.nested import UserNestedSerializer
from workspaces.invitations.serializers.nested import (
    WorkspaceInvitationNestedSerializer,
)
from workspaces.workspaces.serializers.nested import WorkspaceNestedSerializer


class UserSerializer(UserNestedSerializer):
    lang: constr(to_lower=True)


class UserSearchSerializer(UserNestedSerializer):
    user_is_member: bool | None = None
    user_has_pending_invitation: bool | None = None


class VerificationInfoSerializer(BaseModel):
    auth: TokenObtainPairOutputSchema
    project_invitation: ProjectInvitationNestedSerializer | None = None
    workspace_invitation: WorkspaceInvitationNestedSerializer | None = None


class _WorkspaceForDeleteWithProjectsNestedSerializer(WorkspaceNestedSerializer):
    projects: list[ProjectLinkNestedSerializer]


class UserDeleteInfoSerializer(BaseModel):
    only_owner_collective_workspaces: list[WorkspaceNestedSerializer]
    only_owner_collective_projects: list[ProjectNestedSerializer]
    only_member_workspaces: list[_WorkspaceForDeleteWithProjectsNestedSerializer]
    only_member_projects: list[ProjectNestedSerializer]
