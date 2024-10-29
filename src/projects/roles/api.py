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

from base.api.permissions import check_permissions
from base.validators import B64UUID
from exceptions import api as ex
from exceptions.api.errors import ERROR_RESPONSE_400, ERROR_RESPONSE_403, ERROR_RESPONSE_404, ERROR_RESPONSE_422
from ninja_jwt.authentication import AsyncJWTAuth
from permissions import IsProjectAdmin
from projects.projects.api import PermissionsValidator, get_project_or_404
from projects.roles import services as roles_services
from projects.roles.models import ProjectRole
from projects.roles.serializers import ProjectRoleSerializer
from projects.roles.services.exceptions import NonEditableRoleError

# PERMISSIONS
LIST_PROJECT_ROLES = IsProjectAdmin()
UPDATE_PROJECT_ROLE_PERMISSIONS = IsProjectAdmin()


##########################################################
# list roles
##########################################################

roles_router = Router(auth=AsyncJWTAuth())


@roles_router.get(
    "/projects/{project_id}/roles",
    url_name="project.roles.list",
    summary="Get project roles permissions",
    response={
        200: list[ProjectRoleSerializer],
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def list_project_roles(request, project_id: Path[B64UUID]):
    """
    Get project roles and permissions
    """

    project = await get_project_or_404(project_id)
    await check_permissions(permissions=LIST_PROJECT_ROLES, user=request.user, obj=project)
    # noinspection PyTypeChecker
    return await roles_services.list_project_roles(project=project)


##########################################################
# update project role permissions
##########################################################


@roles_router.put(
    "/projects/{project_id}/roles/{role_slug}/permissions",
    url_name="project.roles.permissions.put",
    summary="Edit project roles permissions",
    response={
        200: ProjectRoleSerializer,
        400: ERROR_RESPONSE_400,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def update_project_role_permissions(
    request,
    project_id: Path[B64UUID],
    role_slug: str,
    form: PermissionsValidator,
):
    """
    Edit project roles permissions
    """

    role = await get_project_role_or_404(project_id=project_id, slug=role_slug)
    await check_permissions(permissions=UPDATE_PROJECT_ROLE_PERMISSIONS, user=request.user, obj=role)

    try:
        await roles_services.update_project_role_permissions(role, form.permissions)
    except NonEditableRoleError as exc:
        # change the bad-request into a forbidden error
        raise ex.ForbiddenError(str(exc))
    return role


##########################################################
# misc
##########################################################


async def get_project_role_or_404(project_id: UUID, slug: str) -> ProjectRole:
    role = await roles_services.get_project_role(project_id=project_id, slug=slug)
    if role is None:
        raise ex.NotFoundError(f"Role {slug} does not exist")

    return role
