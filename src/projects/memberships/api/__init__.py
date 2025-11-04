# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 BIRU
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

from ninja import Path, Query, Router

from base.serializers import BaseDataModel
from commons.exceptions import api as ex
from commons.exceptions.api.errors import (
    ERROR_RESPONSE_400,
    ERROR_RESPONSE_403,
    ERROR_RESPONSE_404,
    ERROR_RESPONSE_422,
)
from commons.validators import B64UUID
from memberships.api.validators import DeleteMembershipQuery, MembershipValidator
from memberships.services.exceptions import (
    NonEditableRoleError,
    OwnerRoleNotAuthorisedError,
)
from permissions import check_permissions
from projects.memberships import services as memberships_services
from projects.memberships.api.validators import (
    CreateRoleValidator,
    DeleteRoleQuery,
    UpdateRoleValidator,
)
from projects.memberships.models import ProjectMembership, ProjectRole
from projects.memberships.permissions import (
    ProjectMembershipPermissionsCheck,
    ProjectRolePermissionsCheck,
)
from projects.memberships.serializers import (
    ProjectMembershipSerializer,
    ProjectRoleSerializer,
)
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
        200: BaseDataModel[list[ProjectMembershipSerializer]],
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
    "/projects/memberships/{membership_id}",
    url_name="project.memberships.update",
    summary="Update project membership",
    response={
        200: BaseDataModel[ProjectMembershipSerializer],
        400: ERROR_RESPONSE_400,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def update_project_membership(
    request,
    membership_id: Path[B64UUID],
    form: MembershipValidator,
) -> ProjectMembership:
    """
    Update project membership
    """
    membership = await get_project_membership_or_404(membership_id=membership_id)

    await check_permissions(
        permissions=ProjectMembershipPermissionsCheck.MODIFY.value,
        user=request.user,
        obj=membership,
    )

    try:
        return await memberships_services.update_project_membership(
            membership=membership, role_id=form.role_id, user=request.user
        )
    except OwnerRoleNotAuthorisedError as e:
        raise ex.ForbiddenError(str(e))


##########################################################
# delete project membership
##########################################################


@project_membership_router.delete(
    "/projects/memberships/{membership_id}",
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
    request,
    membership_id: Path[B64UUID],
    query_params: Query[DeleteMembershipQuery],
) -> tuple[int, None]:
    """
    Delete a project membership

    Query params:

    * **successor_user_id:** the user's id who'll inherit the owner role from the user
        - if not received, and user is unique owner of the associated project, an error will be returned
    """
    membership = await get_project_membership_or_404(membership_id=membership_id)

    await check_permissions(
        permissions=ProjectMembershipPermissionsCheck.DELETE.value,
        user=request.user,
        obj=membership,
    )

    await memberships_services.delete_project_membership(
        membership=membership,
        user=request.user,
        successor_user_id=query_params.successor_user_id,
    )
    return 204, None


##########################################################
# list roles
##########################################################


@project_membership_router.get(
    "/projects/{project_id}/roles",
    url_name="project.roles.list",
    summary="List project roles",
    response={
        200: BaseDataModel[list[ProjectRoleSerializer]],
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
        200: BaseDataModel[ProjectRoleSerializer],
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
    form: CreateRoleValidator,
) -> ProjectRole:
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


@project_membership_router.get(
    "/projects/roles/{role_id}",
    url_name="project.roles.get",
    summary="get project role",
    response={
        200: BaseDataModel[ProjectRoleSerializer],
        400: ERROR_RESPONSE_400,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def get_project_role(
    request,
    role_id: Path[B64UUID],
) -> ProjectRole:
    """
    Get project role
    """

    role = await get_project_role_or_404(role_id=role_id, get_members_details=True)
    await check_permissions(
        permissions=ProjectRolePermissionsCheck.VIEW.value,
        user=request.user,
        obj=role.project,
    )
    return role


##########################################################
# update project role
##########################################################


@project_membership_router.patch(
    "/projects/roles/{role_id}",
    url_name="project.roles.patch",
    summary="Update project roles",
    response={
        200: BaseDataModel[ProjectRoleSerializer],
        400: ERROR_RESPONSE_400,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def update_project_role(
    request,
    role_id: Path[B64UUID],
    form: UpdateRoleValidator,
) -> ProjectRole:
    """
    Update project roles
    """

    role = await get_project_role_or_404(role_id=role_id, get_members_details=True)
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


##########################################################
# delete project role
##########################################################


@project_membership_router.delete(
    "/projects/roles/{role_id}",
    url_name="project.roles.delete",
    summary="Delete project roles",
    response={
        204: None,
        400: ERROR_RESPONSE_400,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def delete_project_role(
    request,
    role_id: Path[B64UUID],
    query_params: Query[DeleteRoleQuery],
) -> tuple[int, None]:
    """
    Delete project roles
    """

    role = await get_project_role_or_404(role_id=role_id)
    await check_permissions(
        permissions=ProjectRolePermissionsCheck.DELETE.value,
        user=request.user,
        obj=role,
    )
    try:
        await memberships_services.delete_project_role(
            user=request.user,
            role=role,
            target_role_id=query_params.move_to,
        )
    except (NonEditableRoleError, OwnerRoleNotAuthorisedError) as exc:
        # change the bad-request into a forbidden error
        raise ex.ForbiddenError(str(exc))
    return 204, None


################################################
# misc
################################################


async def get_project_membership_or_404(membership_id: UUID) -> ProjectMembership:
    try:
        membership = await memberships_services.get_project_membership(
            membership_id=membership_id
        )
    except ProjectMembership.DoesNotExist as e:
        raise ex.NotFoundError(f"Membership {membership_id} not found") from e

    return membership


async def get_project_role_or_404(
    role_id: UUID, get_members_details=False
) -> ProjectRole:
    try:
        role = await memberships_services.get_project_role(
            role_id=role_id, get_members_details=get_members_details
        )
    except ProjectRole.DoesNotExist as e:
        raise ex.NotFoundError(f"Role {role_id} does not exist") from e

    return role
