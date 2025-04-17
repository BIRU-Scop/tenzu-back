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

from uuid import UUID

from ninja import Path, Router

from commons.exceptions import api as ex
from commons.exceptions.api.errors import (
    ERROR_RESPONSE_400,
    ERROR_RESPONSE_401,
    ERROR_RESPONSE_403,
    ERROR_RESPONSE_404,
    ERROR_RESPONSE_422,
)
from commons.validators import B64UUID
from permissions import IsAuthenticated, check_permissions
from workspaces.workspaces import services as workspaces_services
from workspaces.workspaces.api.validators import (
    UpdateWorkspaceValidator,
    WorkspaceValidator,
)
from workspaces.workspaces.models import Workspace
from workspaces.workspaces.permissions import WorkspacePermissionsCheck
from workspaces.workspaces.serializers import (
    WorkspaceSerializer,
    WorkspaceWithProjectsSerializer,
)

workspace_router = Router()


##########################################################
# create workspace
##########################################################


@workspace_router.post(
    "/workspaces",
    url_name="workspaces.post",
    summary="Create workspace",
    response={
        200: WorkspaceSerializer,
        403: ERROR_RESPONSE_403,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def create_workspace(request, data: WorkspaceValidator) -> WorkspaceSerializer:
    """
    Create a new workspace for the logged user.
    """
    await check_permissions(
        permissions=WorkspacePermissionsCheck.CREATE.value,
        user=request.user,
    )
    return await workspaces_services.create_workspace(
        name=data.name, color=data.color, created_by=request.user
    )


##########################################################
# list workspaces
##########################################################


@workspace_router.get(
    "/my/workspaces",
    url_name="workspaces.list",
    summary="List the overview of the workspaces to which I belong",
    response={200: list[WorkspaceWithProjectsSerializer], 401: ERROR_RESPONSE_401},
    by_alias=True,
)
async def list_my_workspaces(request) -> list[Workspace]:
    """
    List the workspaces overviews of the logged user.
    """
    await check_permissions(
        permissions=WorkspacePermissionsCheck.VIEW_SELF.value,
        user=request.user,
    )
    return await workspaces_services.list_user_workspaces(user=request.user)


##########################################################
# get workspace
##########################################################


@workspace_router.get(
    "/workspaces/{workspace_id}",
    url_name="workspaces.get",
    summary="Get workspace",
    response={
        200: WorkspaceSerializer,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def get_workspace(request, workspace_id: Path[B64UUID]) -> WorkspaceSerializer:
    """
    Get workspace detail by id.
    """
    workspace = await get_workspace_or_404(workspace_id=workspace_id)
    await check_permissions(
        permissions=WorkspacePermissionsCheck.VIEW.value,
        user=request.user,
        obj=workspace,
    )
    return await workspaces_services.get_user_workspace(
        user=request.user, workspace=workspace
    )


##########################################################
# update workspace
##########################################################


@workspace_router.patch(
    "/workspaces/{workspace_id}",
    url_name="workspace.update",
    summary="Update workspace",
    response={
        200: WorkspaceSerializer,
        400: ERROR_RESPONSE_400,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def update_workspace(
    request,
    workspace_id: Path[B64UUID],
    form: UpdateWorkspaceValidator,
) -> WorkspaceSerializer:
    """
    Update workspace
    """
    workspace = await get_workspace_or_404(workspace_id)
    await check_permissions(
        permissions=WorkspacePermissionsCheck.MODIFY.value,
        user=request.user,
        obj=workspace,
    )

    values = form.dict(exclude_unset=True)
    return await workspaces_services.update_workspace(
        workspace=workspace, user=request.user, values=values
    )


##########################################################
# delete workspace
##########################################################


@workspace_router.delete(
    "/workspaces/{workspace_id}",
    url_name="workspace.delete",
    summary="Delete workspace",
    response={
        204: None,
        400: ERROR_RESPONSE_400,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def delete_workspace(request, workspace_id: Path[B64UUID]) -> tuple[int, None]:
    """
    Delete a workspace
    """
    workspace = await get_workspace_or_404(workspace_id=workspace_id)
    await check_permissions(
        permissions=WorkspacePermissionsCheck.DELETE.value,
        user=request.user,
        obj=workspace,
    )

    await workspaces_services.delete_workspace(
        workspace=workspace, deleted_by=request.user
    )
    return 204, None


##########################################################
# misc
##########################################################


async def get_workspace_or_404(workspace_id: UUID) -> Workspace:
    try:
        workspace = await workspaces_services.get_workspace(workspace_id=workspace_id)
    except Workspace.DoesNotExist:
        raise ex.NotFoundError(f"Workspace {workspace_id} does not exist")

    return workspace
