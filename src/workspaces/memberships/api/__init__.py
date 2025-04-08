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
from permissions import check_permissions
from workspaces.memberships import services as memberships_services
from workspaces.memberships.models import WorkspaceMembership, WorkspaceRole
from workspaces.memberships.permissions import (
    MembershipPermissionsCheck,
    RolePermissionsCheck,
)
from workspaces.memberships.serializers import (
    WorkspaceMembershipSerializer,
)
from workspaces.workspaces.api import get_workspace_or_404

workspace_membership_router = Router()


##########################################################
# list workspace memberships
##########################################################


@workspace_membership_router.get(
    "/workspaces/{id}/memberships",
    url_name="workspace.memberships.list",
    summary="List workspace memberships",
    response={
        200: list[WorkspaceMembershipSerializer],
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def list_workspace_memberships(
    request,
    id: Path[B64UUID],
) -> list[WorkspaceMembership]:
    """
    List workspace memberships
    """
    workspace = await get_workspace_or_404(id)
    await check_permissions(
        permissions=MembershipPermissionsCheck.VIEW.value,
        user=request.user,
        obj=workspace,
    )
    return await memberships_services.list_workspace_memberships(workspace=workspace)


##########################################################
# update workspace membership
##########################################################


@workspace_membership_router.patch(
    "/workspaces/{id}/memberships/{username}",
    url_name="workspace.memberships.update",
    summary="Update workspace membership",
    response={
        200: WorkspaceMembershipSerializer,
        400: ERROR_RESPONSE_400,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def update_workspace_membership(
    request,
    id: Path[B64UUID],
    username: str,
    form: MembershipValidator,
) -> WorkspaceMembership:
    """
    Update workspace membership
    """
    membership = await get_workspace_membership_or_404(
        workspace_id=id, username=username
    )

    await check_permissions(
        permissions=MembershipPermissionsCheck.MODIFY.value,
        user=request.user,
        obj=membership,
    )

    return await memberships_services.update_workspace_membership(
        membership=membership, role_slug=form.role_slug
    )


##########################################################
# delete workspace membership
##########################################################


@workspace_membership_router.delete(
    "/workspaces/{id}/memberships/{username}",
    url_name="workspace.membership.delete",
    summary="Delete workspace membership",
    response={
        204: None,
        400: ERROR_RESPONSE_400,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def delete_workspace_membership(
    request,
    id: Path[B64UUID],
    username: str,
) -> tuple[int, None]:
    """
    Delete a workspace membership
    """
    membership = await get_workspace_membership_or_404(
        workspace_id=id, username=username
    )
    await check_permissions(
        permissions=MembershipPermissionsCheck.DELETE.value,
        user=request.user,
        obj=membership,
    )

    await memberships_services.delete_workspace_membership(membership=membership)

    return 204, None


##########################################################
# list roles
##########################################################


@workspace_membership_router.get(
    "/workspaces/{workspace_id}/roles",
    url_name="workspace.roles.list",
    summary="List workspace roles",
    response={
        200: list[RoleSerializer],
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def list_workspace_roles(request, workspace_id: Path[B64UUID]):
    """
    Get workspace roles and permissions
    """

    workspace = await get_workspace_or_404(workspace_id)
    await check_permissions(
        permissions=RolePermissionsCheck.VIEW.value, user=request.user, obj=workspace
    )
    return await memberships_services.list_workspace_roles(workspace=workspace)


################################################
# misc
################################################


async def get_workspace_membership_or_404(
    workspace_id: UUID, username: str
) -> WorkspaceMembership:
    try:
        membership = await memberships_services.get_workspace_membership(
            workspace_id=workspace_id, username=username
        )
    except WorkspaceMembership.DoesNotExist as e:
        raise ex.NotFoundError(
            f"User {username} is not a member of workspace {workspace_id}"
        ) from e

    return membership


async def get_workspace_role_or_404(workspace_id: UUID, slug: str) -> WorkspaceRole:
    try:
        role = await memberships_services.get_workspace_role(
            workspace_id=workspace_id, slug=slug
        )
    except WorkspaceRole.DoesNotExist as e:
        raise ex.NotFoundError(f"Role {slug} does not exist") from e

    return role
