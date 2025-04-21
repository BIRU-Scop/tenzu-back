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

from ninja import File, Form, Path, Router

from commons.exceptions import api as ex
from commons.exceptions.api.errors import (
    ERROR_RESPONSE_400,
    ERROR_RESPONSE_403,
    ERROR_RESPONSE_404,
    ERROR_RESPONSE_422,
)
from commons.validators import B64UUID
from permissions import (
    check_permissions,
)
from projects.projects import services as projects_services
from projects.projects.api.validators import (
    CreateProjectValidator,
    LogoField,
    UpdateProjectValidator,
)
from projects.projects.models import Project
from projects.projects.permissions import ProjectPermissionsCheck
from projects.projects.serializers import (
    ProjectDetailSerializer,
    ProjectSummarySerializer,
)
from workspaces.workspaces.api import get_workspace_or_404
from workspaces.workspaces.permissions import WorkspacePermissionsCheck

projects_router = Router()


##########################################################
# create project
##########################################################


@projects_router.post(
    "/workspaces/{workspace_id}/projects",
    url_name="projects.create",
    summary="Create projects",
    response={
        200: ProjectDetailSerializer,
        400: ERROR_RESPONSE_404,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    tags=["workspaces", "projects"],
    by_alias=True,
)
async def create_project(
    request,
    workspace_id: Path[B64UUID],
    form: Form[CreateProjectValidator],
    logo: LogoField | None = File(None),
) -> ProjectDetailSerializer:
    """
    Create project in a given workspace.
    """
    workspace = await get_workspace_or_404(workspace_id=workspace_id)

    await check_permissions(
        permissions=ProjectPermissionsCheck.CREATE.value,
        user=request.user,
        obj=workspace,
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
    tags=["workspaces", "projects"],
    by_alias=True,
)
async def list_workspace_projects(
    request, workspace_id: Path[B64UUID]
) -> list[Project]:
    """
    List projects of a workspace visible by the user.
    """
    workspace = await get_workspace_or_404(workspace_id=workspace_id)
    await check_permissions(
        permissions=WorkspacePermissionsCheck.VIEW.value,
        user=request.user,
        obj=workspace,
    )
    return await projects_services.list_workspace_projects_for_user(
        workspace=workspace, user=request.user
    )


##########################################################
# get project
##########################################################


@projects_router.get(
    "/projects/{project_id}",
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
async def get_project(request, project_id: Path[B64UUID]) -> ProjectDetailSerializer:
    """
    Get project detail by id.
    """

    project = await get_project_or_404(project_id)
    await check_permissions(
        permissions=ProjectPermissionsCheck.VIEW.value, user=request.user, obj=project
    )
    return await projects_services.get_project_detail(
        project=project, user=request.user
    )


##########################################################
# update project
##########################################################


# WARNING: route has been passed from PATCH  to POST
# Django ninja ignored Form data (by multiform or url-encode) if it's not a POST route
@projects_router.post(
    "/projects/{project_id}",
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
    project_id: Path[B64UUID],
    form: Form[UpdateProjectValidator],
    logo: LogoField | None = File(None),
) -> ProjectDetailSerializer:
    """
    Update project
    """
    project = await get_project_or_404(project_id)
    await check_permissions(
        permissions=ProjectPermissionsCheck.MODIFY.value, user=request.user, obj=project
    )

    values = form.model_dump(exclude_unset=True)
    # if a file is present, we need to assign it
    if "logo" in request.POST or request.FILES:
        values["logo"] = logo
    return await projects_services.update_project(
        project=project, updated_by=request.user, values=values
    )


##########################################################
# delete project
##########################################################


@projects_router.delete(
    "/projects/{project_id}",
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
    project_id: Path[B64UUID],
) -> tuple[int, None]:
    """
    Delete a project
    """
    project = await get_project_or_404(project_id)
    await check_permissions(
        permissions=ProjectPermissionsCheck.DELETE.value, user=request.user, obj=project
    )

    await projects_services.delete_project(project=project, deleted_by=request.user)
    return 204, None


##########################################################
# misc get project or 404
##########################################################


async def get_project_or_404(project_id: UUID) -> Project:
    try:
        project = await projects_services.get_project(id=project_id)
    except Project.DoesNotExist as e:
        raise ex.NotFoundError("Project does not exist") from e

    return project
