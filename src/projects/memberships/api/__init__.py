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
from memberships.api.validators import MembershipValidator
from memberships.serializers import RoleSerializer
from memberships.services.exceptions import (
    NonEditableRoleError,
    OwnerRoleNotAuthorisedError,
)
from permissions import check_permissions
from projects.memberships import services as memberships_services
from projects.memberships.api.validators import RoleCreateValidator, RoleUpdateValidator
from projects.memberships.models import ProjectMembership, ProjectRole
from projects.memberships.permissions import (
    ProjectMembershipPermissionsCheck,
    ProjectRolePermissionsCheck,
)
from projects.memberships.serializers import ProjectMembershipSerializer
from projects.projects.api import get_project_or_404

project_membership_router = Router()


##########################################################
# list project memberships
##########################################################


@project_membership_router.get(
    "/projects/{project_id}/memberships",
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
    project_id: Path[B64UUID],
) -> list[ProjectMembership]:
    """
    List project memberships
    """
    project = await get_project_or_404(project_id)
    await check_permissions(
        permissions=ProjectMembershipPermissionsCheck.VIEW.value,
        user=request.user,
        obj=project,
    )
    return await memberships_services.list_project_memberships(project=project)


##########################################################
# update project membership
##########################################################


@project_membership_router.patch(
    "/projects/{project_id}/memberships/{username}",
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
    project_id: Path[B64UUID],
    username: Path[str],
    form: MembershipValidator,
) -> ProjectMembership:
    """
    Update project membership
    """
    membership = await get_project_membership_or_404(
        project_id=project_id, username=username
    )

    await check_permissions(
        permissions=ProjectMembershipPermissionsCheck.MODIFY.value,
        user=request.user,
        obj=membership,
    )

    try:
        return await memberships_services.update_project_membership(
            membership=membership, role_slug=form.role_slug, user=request.user
        )
    except OwnerRoleNotAuthorisedError as e:
        raise ex.ForbiddenError(str(e))


##########################################################
# delete project membership
##########################################################


@project_membership_router.delete(
    "/projects/{project_id}/memberships/{username}",
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
    request, project_id: Path[B64UUID], username: Path[str]
) -> tuple[int, None]:
    """
    Delete a project membership
    """
    membership = await get_project_membership_or_404(
        project_id=project_id, username=username
    )

    await check_permissions(
        permissions=ProjectMembershipPermissionsCheck.DELETE.value,
        user=request.user,
        obj=membership,
    )

    await memberships_services.delete_project_membership(membership=membership)
    return 204, None


##########################################################
# list roles
##########################################################


@project_membership_router.get(
    "/projects/{project_id}/roles",
    url_name="project.roles.list",
    summary="List project roles",
    response={
        200: list[RoleSerializer],
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
    await check_permissions(
        permissions=ProjectRolePermissionsCheck.VIEW.value,
        user=request.user,
        obj=project,
    )
    return await memberships_services.list_project_roles(project=project)


##########################################################
# create project role
##########################################################


@project_membership_router.post(
    "/projects/{project_id}/roles",
    url_name="project.roles.create",
    summary="Create project roles",
    response={
        200: RoleSerializer,
        400: ERROR_RESPONSE_400,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def create_project_role(
    request,
    project_id: Path[B64UUID],
    form: RoleCreateValidator,
):
    """
    Create project roles
    """
    project = await get_project_or_404(project_id)
    await check_permissions(
        permissions=ProjectRolePermissionsCheck.CREATE.value,
        user=request.user,
        obj=project,
    )
    values = form.model_dump(exclude_unset=True)

    return await memberships_services.create_project_role(
        project_id=project.id, **values
    )


##########################################################
# update project role
##########################################################


@project_membership_router.put(
    "/projects/{project_id}/roles/{role_slug}",
    url_name="project.roles.put",
    summary="Edit project roles",
    response={
        200: RoleSerializer,
        400: ERROR_RESPONSE_400,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def update_project_role(
    request,
    project_id: Path[B64UUID],
    role_slug: Path[str],
    form: RoleUpdateValidator,
):
    """
    Edit project roles
    """

    role = await get_project_role_or_404(project_id=project_id, slug=role_slug)
    await check_permissions(
        permissions=ProjectRolePermissionsCheck.MODIFY.value,
        user=request.user,
        obj=role,
    )
    values = form.model_dump(exclude_unset=True)

    try:
        return await memberships_services.update_project_role(role, values)
    except NonEditableRoleError as exc:
        # change the bad-request into a forbidden error
        raise ex.ForbiddenError(str(exc))


# TODO create and delete api (for delete, have replacement role for existing users and pending invitations) take care of editable attribute

################################################
# misc
################################################


async def get_project_membership_or_404(
    project_id: UUID, username: str
) -> ProjectMembership:
    try:
        membership = await memberships_services.get_project_membership(
            project_id=project_id, username=username
        )
    except ProjectMembership.DoesNotExist as e:
        raise ex.NotFoundError(
            f"User {username} is not a member of project {project_id}"
        ) from e

    return membership


async def get_project_role_or_404(project_id: UUID, slug: str) -> ProjectRole:
    try:
        role = await memberships_services.get_project_role(
            project_id=project_id, slug=slug
        )
    except ProjectRole.DoesNotExist as e:
        raise ex.NotFoundError(f"Role {slug} does not exist") from e

    return role
