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
    LogoField,
    ProjectValidator,
    UpdateProjectValidator,
)
from projects.projects.models import Project
from projects.projects.permissions import ProjectPermissionsCheck
from projects.projects.serializers import (
    ProjectDetailSerializer,
)
from workspaces.workspaces import services as workspaces_services
from workspaces.workspaces.models import Workspace

projects_router = Router()


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
    logo: LogoField | None = File(None),
) -> ProjectDetailSerializer:
    """
    Create project in a given workspace.
    """
    try:
        workspace = await workspaces_services.get_workspace(
            workspace_id=form.workspace_id
        )
    except Workspace.DoesNotExist:
        raise ex.BadRequest(f"Workspace {form.workspace_id} does not exist")

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
    await check_permissions(
        permissions=ProjectPermissionsCheck.DELETE.value, user=request.user, obj=project
    )

    await projects_services.delete_project(project=project, deleted_by=request.user)
    return 204, None


##########################################################
# misc get project or 404
##########################################################


async def get_project_or_404(id: UUID) -> Project:
    project = await projects_services.get_project(id=id)
    if project is None:
        raise ex.NotFoundError("Project does not exist")

    return project
