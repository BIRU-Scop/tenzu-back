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
from exceptions.api.errors import (
    ERROR_RESPONSE_400,
    ERROR_RESPONSE_403,
    ERROR_RESPONSE_404,
    ERROR_RESPONSE_422,
)
from ninja_jwt.authentication import AsyncJWTAuth
from permissions import CanViewProject, IsProjectAdmin, IsRelatedToTheUser
from projects.memberships import services as memberships_services
from projects.memberships.api.validators import ProjectMembershipValidator
from projects.memberships.models import ProjectMembership
from projects.memberships.serializers import ProjectMembershipSerializer
from projects.projects.api import get_project_or_404

membership_router = Router(auth=AsyncJWTAuth())

# PERMISSIONS
LIST_PROJECT_MEMBERSHIPS = CanViewProject()
UPDATE_PROJECT_MEMBERSHIP = IsProjectAdmin()
DELETE_PROJECT_MEMBERSHIP = IsProjectAdmin() | IsRelatedToTheUser("user")


##########################################################
# list project memberships
##########################################################


@membership_router.get(
    "/projects/{id}/memberships",
    url_name="project.memberships.list",
    summary="List project memberships",
    response={
        200: list[ProjectMembershipSerializer],
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def list_project_memberships(
    request,
    id: Path[B64UUID],
) -> list[ProjectMembership]:
    """
    List project memberships
    """

    project = await get_project_or_404(id)
    await check_permissions(
        permissions=LIST_PROJECT_MEMBERSHIPS, user=request.user, obj=project
    )
    return await memberships_services.list_project_memberships(project=project)


##########################################################
# update project membership
##########################################################


@membership_router.patch(
    "/projects/{id}/memberships/{username}",
    url_name="project.memberships.update",
    summary="Update project membership",
    response={
        200: ProjectMembershipSerializer,
        400: ERROR_RESPONSE_400,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def update_project_membership(
    request,
    id: Path[B64UUID],
    username: str,
    form: ProjectMembershipValidator,
) -> ProjectMembership:
    """
    Update project membership
    """
    membership = await get_project_membership_or_404(project_id=id, username=username)

    await check_permissions(
        permissions=UPDATE_PROJECT_MEMBERSHIP, user=request.user, obj=membership
    )

    return await memberships_services.update_project_membership(
        membership=membership, role_slug=form.role_slug
    )


##########################################################
# delete project membership
##########################################################


@membership_router.delete(
    "/projects/{id}/memberships/{username}",
    url_name="project.memberships.delete",
    summary="Delete project membership",
    response={
        204: None,
        400: ERROR_RESPONSE_400,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def delete_project_membership(
    request, id: Path[B64UUID], username: str
) -> tuple[int, None]:
    """
    Delete a project membership
    """
    membership = await get_project_membership_or_404(project_id=id, username=username)

    await check_permissions(
        permissions=DELETE_PROJECT_MEMBERSHIP, user=request.user, obj=membership
    )

    await memberships_services.delete_project_membership(membership=membership)
    return 204, None


################################################
# misc
################################################


async def get_project_membership_or_404(
    project_id: UUID, username: str
) -> ProjectMembership:
    membership = await memberships_services.get_project_membership(
        project_id=project_id, username=username
    )
    if not membership:
        raise ex.NotFoundError("Membership not found")

    return membership
