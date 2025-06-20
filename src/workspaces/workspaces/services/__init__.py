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

from commons.utils import transaction_atomic_async, transaction_on_commit_async
from permissions.choices import WorkspacePermissions
from projects.projects import repositories as projects_repositories
from users.models import User
from workspaces.memberships import repositories as ws_memberships_repositories
from workspaces.memberships.models import WorkspaceRole
from workspaces.workspaces import events as workspaces_events
from workspaces.workspaces import repositories as workspaces_repositories
from workspaces.workspaces.models import Workspace
from workspaces.workspaces.serializers import WorkspaceDetailSerializer
from workspaces.workspaces.services import exceptions as ex

##########################################################
# create workspace
##########################################################


async def create_workspace(
    name: str, color: int, created_by: User
) -> WorkspaceDetailSerializer:
    workspace, owner_role = await _create_workspace(
        name=name, color=color, created_by=created_by
    )
    workspace_detail = WorkspaceDetailSerializer(
        id=workspace.id,
        name=workspace.name,
        slug=workspace.slug,
        color=workspace.color,
        user_role=owner_role,
        user_is_invited=False,
        user_is_member=True,
        user_can_create_projects=True,
        total_projects=0,
    )
    await transaction_on_commit_async(
        workspaces_events.emit_event_when_workspace_is_created
    )(workspace_detail=workspace_detail, created_by=created_by)
    return workspace_detail


@transaction_atomic_async
async def _create_workspace(
    name: str, color: int, created_by: User
) -> tuple[Workspace, WorkspaceRole]:
    workspace = await workspaces_repositories.create_workspace(
        name=name, color=color, created_by=created_by
    )
    owner_role = (
        await ws_memberships_repositories.bulk_create_workspace_default_roles(workspace)
    )[0]
    await ws_memberships_repositories.create_workspace_membership(
        user=created_by, workspace=workspace, role=owner_role
    )
    return workspace, owner_role


##########################################################
# list workspace
##########################################################


async def list_user_workspaces(user: User) -> list[Workspace]:
    return await workspaces_repositories.list_user_workspaces_overview(user=user)


##########################################################
# get workspace
##########################################################


async def get_workspace(
    workspace_id: UUID, get_total_project=False
) -> Workspace | None:
    return await workspaces_repositories.get_workspace(
        workspace_id=workspace_id, get_total_project=get_total_project
    )


async def get_user_workspace(
    user: User, workspace: Workspace
) -> WorkspaceDetailSerializer:
    return WorkspaceDetailSerializer(
        id=workspace.id,
        name=workspace.name,
        slug=workspace.slug,
        color=workspace.color,
        user_role=user.workspace_role,
        user_is_invited=user.is_invited or False,
        user_is_member=user.workspace_role is not None,
        user_can_create_projects=(
            user.workspace_role is not None
            and (
                WorkspacePermissions.CREATE_PROJECT.value
                in user.workspace_role.permissions
            )
        ),
        total_projects=workspace.total_projects,
    )


##########################################################
# update workspace
##########################################################


async def update_workspace(
    workspace: Workspace, user: User, values: dict[str, Any] = {}
) -> WorkspaceDetailSerializer:
    workspace = await _update_workspace(workspace=workspace, values=values)
    workspace_detail = WorkspaceDetailSerializer(
        id=workspace.id,
        name=workspace.name,
        slug=workspace.slug,
        color=workspace.color,
        user_role=user.workspace_role,
        user_is_invited=False,
        user_is_member=user.workspace_role is not None,
        user_can_create_projects=(
            user.workspace_role is not None
            and (
                WorkspacePermissions.CREATE_PROJECT.value
                in user.workspace_role.permissions
            )
        ),
        total_projects=workspace.total_projects,
    )
    await workspaces_events.emit_event_when_workspace_is_updated(
        workspace_detail=workspace_detail, updated_by=user
    )
    return workspace_detail


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
