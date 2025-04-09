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

from workspaces.workspaces.models import Workspace
from workspaces.workspaces.serializers import (
    WorkspaceDetailSerializer,
    WorkspaceSerializer,
)
from workspaces.workspaces.serializers.nested import WorkspaceNestedSerializer

# TODO refactor this with new role info and reduce number of different endpoints


def serialize_workspace(
    workspace: Workspace, user_role: str, total_projects: int
) -> WorkspaceSerializer:
    return WorkspaceSerializer(
        id=workspace.id,
        name=workspace.name,
        slug=workspace.slug,
        color=workspace.color,
        total_projects=total_projects,
        has_projects=workspace.has_projects,  # type: ignore[attr-defined]
        user_role=user_role,
    )


def serialize_workspace_detail(workspace: Workspace) -> WorkspaceDetailSerializer:
    return WorkspaceDetailSerializer(
        id=workspace.id,
        name=workspace.name,
        slug=workspace.slug,
        color=workspace.color,
        latest_projects=workspace.latest_projects,  # type: ignore[attr-defined]
        invited_projects=workspace.invited_projects,  # type: ignore[attr-defined]
        total_projects=workspace.total_projects,  # type: ignore[attr-defined]
        has_projects=workspace.has_projects,  # type: ignore[attr-defined]
        user_role=workspace.user_role,  # type: ignore[attr-defined]
    )


def serialize_nested(workspace: Workspace) -> WorkspaceNestedSerializer:
    return WorkspaceNestedSerializer(
        id=workspace.id,
        name=workspace.name,
        slug=workspace.slug,
    )
