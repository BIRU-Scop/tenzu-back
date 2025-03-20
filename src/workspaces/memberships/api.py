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
    ERROR_RESPONSE_403,
    ERROR_RESPONSE_404,
    ERROR_RESPONSE_422,
)
from commons.validators import B64UUID
from permissions import check_permissions
from workspaces.memberships import services as memberships_services
from workspaces.memberships.models import WorkspaceMembership
from workspaces.memberships.permissions import MembershipPermissionsCheck
from workspaces.memberships.serializers import (
    WorkspaceMembershipDetailSerializer,
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
        200: list[WorkspaceMembershipDetailSerializer],
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def list_workspace_memberships(
    request,
    id: Path[B64UUID],
) -> list[WorkspaceMembershipDetailSerializer]:
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
# delete workspace membership
##########################################################


@workspace_membership_router.delete(
    "/workspaces/{id}/memberships/{username}",
    url_name="workspace.membership.delete",
    summary="Delete workspace membership",
    response={204: None, 403: ERROR_RESPONSE_403, 404: ERROR_RESPONSE_404},
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
        obj=membership.workspace,
    )

    await memberships_services.delete_workspace_membership(membership=membership)

    return 204, None


################################################
# misc: get workspace membership or 404
################################################


async def get_workspace_membership_or_404(
    workspace_id: UUID, username: str
) -> WorkspaceMembership:
    membership = await memberships_services.get_workspace_membership(
        workspace_id=workspace_id, username=username
    )
    if membership is None:
        raise ex.NotFoundError(
            f"User {username} is not a member of workspace {workspace_id}"
        )

    return membership
