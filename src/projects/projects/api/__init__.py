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

from typing import Optional
from uuid import UUID

from ninja import File, Form, Path, Router

from base.api.permissions import check_permissions
from base.validators import B64UUID
from exceptions import api as ex
from exceptions.api.errors import (
    ERROR_RESPONSE_400,
    ERROR_RESPONSE_401,
    ERROR_RESPONSE_403,
    ERROR_RESPONSE_404,
    ERROR_RESPONSE_422,
)
from ninja_jwt.authentication import AsyncJWTAuth
from permissions import (
    CanViewProject,
    HasPerm,
    IsAuthenticated,
    IsProjectAdmin,
    IsWorkspaceMember,
)
from permissions import services as permissions_services
from projects.projects import services as projects_services
from projects.projects.api.validators import (
    LogoField,
    PermissionsValidator,
    ProjectValidator,
    UpdateProjectValidator,
)
from projects.projects.models import Project
from projects.projects.serializers import (
    ProjectDetailSerializer,
    ProjectSummarySerializer,
)
from workspaces.workspaces import services as workspaces_services
from workspaces.workspaces.api import get_workspace_or_404

# PERMISSIONS
CREATE_PROJECT = HasPerm("view_workspace")
LIST_WORKSPACE_PROJECTS = IsAuthenticated()  # HasPerm("view_workspace")
LIST_WORKSPACE_INVITED_PROJECTS = IsAuthenticated()  # HasPerm("view_workspace")
GET_PROJECT = CanViewProject()
UPDATE_PROJECT = IsProjectAdmin()
GET_PROJECT_PUBLIC_PERMISSIONS = IsProjectAdmin()
UPDATE_PROJECT_PUBLIC_PERMISSIONS = IsProjectAdmin()
DELETE_PROJECT = IsProjectAdmin() | IsWorkspaceMember()

projects_router = Router(auth=AsyncJWTAuth())


##########################################################
# create project
##########################################################


@projects_router.post(
    "/projects",
    url_name="projects.create",
    summary="Create projects",
    response={
        200: ProjectDetailSerializer,
        400: ERROR_RESPONSE_404,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def create_project(
    request,
    form: Form[ProjectValidator],
    logo: Optional[LogoField] = File(None),
) -> ProjectDetailSerializer:
    """
    Create project in a given workspace.
    """
    workspace = await workspaces_services.get_workspace(id=form.workspace_id)
    if workspace is None:
        raise ex.BadRequest(f"Workspace {form.workspace_id} does not exist")

    await check_permissions(
        permissions=CREATE_PROJECT, user=request.user, obj=workspace
    )
    return await projects_services.create_project(
        workspace=workspace,
        name=form.name,
        description=form.description,
        color=form.color,
        created_by=request.user,
        logo=logo,
    )


##########################################################
# list projects
##########################################################


@projects_router.get(
    "/workspaces/{workspace_id}/projects",
    url_name="workspace.projects.list",
    summary="List workspace projects",
    response={
        200: list[ProjectSummarySerializer],
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def list_workspace_projects(
    request, workspace_id: Path[B64UUID]
) -> list[Project]:
    """
    List projects of a workspace visible by the user.
    """
    workspace = await get_workspace_or_404(id=workspace_id)
    await check_permissions(
        permissions=LIST_WORKSPACE_PROJECTS, user=request.user, obj=workspace
    )
    return await projects_services.list_workspace_projects_for_user(
        workspace=workspace, user=request.user
    )


@projects_router.get(
    "/workspaces/{workspace_id}/invited-projects",
    url_name="workspace.invited-projects.list",
    summary="List of projects in a workspace where the user is invited",
    response={
        200: list[ProjectSummarySerializer],
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def list_workspace_invited_projects(
    request, workspace_id: Path[B64UUID]
) -> list[Project]:
    """
    Get all the invitations to projects that  a user has in a workspace
    """
    workspace = await get_workspace_or_404(id=workspace_id)
    await check_permissions(
        permissions=LIST_WORKSPACE_INVITED_PROJECTS, user=request.user, obj=workspace
    )
    return await projects_services.list_workspace_invited_projects_for_user(
        workspace=workspace, user=request.user
    )


##########################################################
# get project
##########################################################


@projects_router.get(
    "/projects/{id}",
    url_name="project.get",
    summary="Get project",
    response={
        200: ProjectDetailSerializer,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def get_project(request, id: Path[B64UUID]) -> ProjectDetailSerializer:
    """
    Get project detail by id.
    """

    project = await get_project_or_404(id)
    await check_permissions(permissions=GET_PROJECT, user=request.user, obj=project)
    return await projects_services.get_project_detail(
        project=project, user=request.user
    )


@projects_router.get(
    "/projects/{id}/public-permissions",
    url_name="project.public-permissions.list",
    summary="List project public permissions",
    response={
        200: list[str],
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def list_project_public_permissions(request, id: Path[B64UUID]) -> list[str]:
    """
    Get project public permissions
    """

    project = await get_project_or_404(id)
    await check_permissions(
        permissions=GET_PROJECT_PUBLIC_PERMISSIONS, user=request.user, obj=project
    )
    return project.public_permissions or []


##########################################################
# update project
##########################################################


# WARNING: route has been passed from PATCH  to POST
# Django ninja ignored Form data (by multiform or url-encode) if it's not a POST route
@projects_router.post(
    "/projects/{id}",
    url_name="project.update",
    summary="Update project",
    response={
        200: ProjectDetailSerializer,
        400: ERROR_RESPONSE_400,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def update_project(
    request,
    id: Path[B64UUID],
    form: Form[UpdateProjectValidator],
    logo: LogoField | None = File(None),
) -> ProjectDetailSerializer:
    """
    Update project
    """
    project = await get_project_or_404(id)
    await check_permissions(permissions=UPDATE_PROJECT, user=request.user, obj=project)

    # if a file is present, we need to assign it
    if logo is not None:
        form.logo = logo
    values = form.model_dump(exclude_unset=True)
    return await projects_services.update_project(
        project=project, user=request.user, values=values
    )


@projects_router.put(
    "/projects/{id}/public-permissions",
    url_name="project.public-permissions.put",
    summary="Edit project public permissions",
    response={
        200: list[str],
        400: ERROR_RESPONSE_400,
        401: ERROR_RESPONSE_401,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def update_project_public_permissions(
    request,
    id: Path[B64UUID],
    form: PermissionsValidator,
) -> list[str]:
    """
    Edit project public permissions
    """

    project = await get_project_or_404(id)
    await check_permissions(
        permissions=UPDATE_PROJECT_PUBLIC_PERMISSIONS, user=request.user, obj=project
    )

    return await projects_services.update_project_public_permissions(
        project, form.permissions
    )


##########################################################
# delete project
##########################################################


@projects_router.delete(
    "/projects/{id}",
    url_name="projects.delete",
    summary="Delete project",
    response={
        204: None,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def delete_project(
    request,
    id: Path[B64UUID],
) -> tuple[int, None]:
    """
    Delete a project
    """
    project = await get_project_or_404(id)
    await check_permissions(permissions=DELETE_PROJECT, user=request.user, obj=project)

    await projects_services.delete_project(project=project, deleted_by=request.user)
    return 204, None


##########################################################
# misc permissions
##########################################################


@projects_router.get(
    "/my/projects/{id}/permissions",
    url_name="my.projects.permissions.list",
    summary="List my project permissions",
    response={
        200: list[str],
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def list_my_project_permissions(request, id: Path[B64UUID]) -> list[str]:
    """
    List the computed permissions a user has over a project.
    """
    project = await get_project_or_404(id)
    return await permissions_services.get_user_permissions(
        user=request.user, obj=project
    )


##########################################################
# misc get project or 404
##########################################################


async def get_project_or_404(id: UUID) -> Project:
    project = await projects_services.get_project(id=id)
    if project is None:
        raise ex.NotFoundError("Project does not exist")

    return project
