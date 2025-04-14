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
    WorkspaceDetailSerializer,
    WorkspaceSerializer,
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
    url_name="workspaces.post",
    summary="List the overview of the workspaces to which I belong",
    response={200: list[WorkspaceDetailSerializer], 403: ERROR_RESPONSE_403},
    by_alias=True,
)
async def list_my_workspaces(request) -> list[WorkspaceDetailSerializer]:
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
    "/workspaces/{id}",
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
async def get_workspace(request, id: Path[B64UUID]) -> WorkspaceSerializer:
    """
    Get workspace detail by id.
    """
    workspace = await get_workspace_or_404(id=id)
    await check_permissions(
        permissions=WorkspacePermissionsCheck.VIEW.value,
        user=request.user,
        obj=workspace,
    )
    return await workspaces_services.get_workspace_detail(
        id=workspace.id, user_id=request.user.id
    )


@workspace_router.get(
    "/my/workspaces/{id}",
    url_name="my.workspaces.get",
    summary="Get the overview of a workspace to which I belong",
    response={
        200: WorkspaceDetailSerializer,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def get_my_workspace(request, id: Path[B64UUID]) -> WorkspaceDetailSerializer:
    """
    Get the workspaces overview for the logged user.
    """
    # TODO only keep one of "get_workspace" api, check membership permission and simplify get_user_workspace_overview
    await check_permissions(
        permissions=WorkspacePermissionsCheck.VIEW_SELF.value,
        user=request.user,
    )
    workspace_overview = await workspaces_services.get_user_workspace(
        user=request.user, workspace_id=id
    )
    if workspace_overview is None:
        raise ex.NotFoundError(f"Workspace {id} does not exist")
    return workspace_overview


##########################################################
# update workspace
##########################################################


@workspace_router.patch(
    "/workspaces/{id}",
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
    id: Path[B64UUID],
    form: UpdateWorkspaceValidator,
) -> WorkspaceSerializer:
    """
    Update workspace
    """
    workspace = await get_workspace_or_404(id)
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
    "/workspaces/{id}",
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
async def delete_workspace(request, id: Path[B64UUID]) -> tuple[int, None]:
    """
    Delete a workspace
    """
    workspace = await get_workspace_or_404(id=id)
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


async def get_workspace_or_404(id: UUID) -> Workspace:
    workspace = await workspaces_services.get_workspace(workspace_id=id)
    if workspace is None:
        raise ex.NotFoundError(f"Workspace {id} does not exist")

    return workspace
