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

from typing import Any, cast
from uuid import UUID

from projects.projects import repositories as projects_repositories
from users.models import User
from workspaces.memberships import repositories as ws_memberships_repositories
from workspaces.memberships import services as ws_memberships_services
from workspaces.memberships.services import get_workspace_role_name
from workspaces.workspaces import events as workspaces_events
from workspaces.workspaces import repositories as workspaces_repositories
from workspaces.workspaces.models import Workspace
from workspaces.workspaces.serializers import (
    WorkspaceDetailSerializer,
    WorkspaceSerializer,
)
from workspaces.workspaces.serializers import services as serializers_services
from workspaces.workspaces.serializers.nested import WorkspaceNestedSerializer
from workspaces.workspaces.services import exceptions as ex

##########################################################
# create workspace
##########################################################


async def create_workspace(
    name: str, color: int, created_by: User
) -> WorkspaceSerializer:
    workspace = await _create_workspace(name=name, color=color, created_by=created_by)
    return await get_workspace_detail(id=workspace.id, user_id=created_by.id)


#  TODO: review this method after the sampledata refactor
async def _create_workspace(name: str, color: int, created_by: User) -> Workspace:
    workspace = await workspaces_repositories.create_workspace(
        name=name, color=color, created_by=created_by
    )
    await ws_memberships_repositories.create_workspace_membership(
        user=created_by, workspace=workspace
    )
    return workspace


##########################################################
# list workspace
##########################################################


async def list_user_workspaces(user: User) -> list[WorkspaceDetailSerializer]:
    return [
        serializers_services.serialize_workspace_detail(workspace=workspace)
        for workspace in await workspaces_repositories.list_user_workspaces_overview(
            user=user
        )
    ]


##########################################################
# get workspace
##########################################################


async def get_workspace(workspace_id: UUID) -> Workspace | None:
    return await workspaces_repositories.get_workspace(workspace_id=workspace_id)


async def get_workspace_detail(id: UUID, user_id: UUID | None) -> WorkspaceSerializer:
    workspace = cast(
        Workspace,
        await workspaces_repositories.get_workspace_detail(
            workspace_id=id, user_id=user_id
        ),
    )
    return serializers_services.serialize_workspace(
        workspace=workspace,
        user_role=await ws_memberships_services.get_workspace_role_name(
            workspace_id=id, user_id=user_id
        ),
        total_projects=(
            await projects_repositories.get_total_projects(
                workspace_id=id, filters={"memberships__user_id": user_id}
            )
            if user_id
            else 0
        ),
    )


async def get_workspace_nested(
    workspace_id: UUID, user_id: UUID | None
) -> WorkspaceNestedSerializer:
    # TODO: this service should be improved
    workspace = cast(
        Workspace,
        await workspaces_repositories.get_workspace_summary(
            workspace_id=workspace_id,
        ),
    )
    return serializers_services.serialize_nested(
        workspace=workspace,
        user_role=await get_workspace_role_name(
            workspace_id=workspace_id, user_id=user_id
        ),
    )


async def get_user_workspace(
    user: User, workspace_id: UUID
) -> WorkspaceDetailSerializer | None:
    workspace = await workspaces_repositories.get_user_workspace_overview(
        user=user, id=workspace_id
    )
    if workspace:
        return serializers_services.serialize_workspace_detail(workspace=workspace)

    return None


##########################################################
# update workspace
##########################################################


async def update_workspace(
    workspace: Workspace, user: User, values: dict[str, Any] = {}
) -> WorkspaceSerializer:
    updated_workspace = await _update_workspace(workspace=workspace, values=values)
    return await get_workspace_detail(id=updated_workspace.id, user_id=user.id)


async def _update_workspace(
    workspace: Workspace, values: dict[str, Any] = {}
) -> Workspace:
    # Prevent hitting the database with an empty PATCH
    if not values:
        return workspace

    if "name" in values and values["name"] is None:
        raise ex.TenzuValidationError("Name cannot be null")

    return await workspaces_repositories.update_workspace(
        workspace=workspace, values=values
    )


##########################################################
# delete workspace
##########################################################


async def delete_workspace(workspace: Workspace, deleted_by: User) -> bool:
    ws_total_projects = await projects_repositories.get_total_projects(
        workspace_id=workspace.id
    )
    if ws_total_projects:
        raise ex.WorkspaceHasProjects(
            f"This workspace has {ws_total_projects} projects. Delete the projects and try again."
        )

    deleted = await workspaces_repositories.delete_workspace(workspace_id=workspace.id)
    if deleted > 0:
        await workspaces_events.emit_event_when_workspace_is_deleted(
            workspace=workspace, deleted_by=deleted_by
        )
        return True

    return False
