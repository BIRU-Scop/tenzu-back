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

from ninja_jwt.schema import TokenObtainPairOutputSchema
from projects.invitations.models import ProjectInvitation
from projects.projects.models import Project
from users.serializers import (
    UserDeleteInfoSerializer,
    VerificationInfoSerializer,
    _WorkspaceWithProjectsNestedSerializer,
)
from workspaces.invitations.models import WorkspaceInvitation
from workspaces.workspaces.models import Workspace


def serialize_verification_info(
    auth: TokenObtainPairOutputSchema,
    project_invitation: ProjectInvitation | None,
    workspace_invitation: WorkspaceInvitation | None,
) -> VerificationInfoSerializer:
    return VerificationInfoSerializer(
        auth=auth,
        project_invitation=project_invitation,
        workspace_invitation=workspace_invitation,
    )


def serialize_workspace_with_projects_nested(
    workspace: Workspace, projects: list[Project] = []
) -> _WorkspaceWithProjectsNestedSerializer:
    return _WorkspaceWithProjectsNestedSerializer(
        id=workspace.id,
        name=workspace.name,
        slug=workspace.slug,
        color=workspace.color,
        projects=projects,
    )


def serialize_user_delete_info(
    workspaces: list[_WorkspaceWithProjectsNestedSerializer],
    projects: list[Project] = [],
) -> UserDeleteInfoSerializer:
    return UserDeleteInfoSerializer(
        workspaces=workspaces,
        projects=projects,
    )
