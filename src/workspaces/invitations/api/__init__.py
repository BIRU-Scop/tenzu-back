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

from ninja import Path, Router

from base.validators import B64UUID
from commons.exceptions import api as ex
from commons.exceptions.api.errors import (
    ERROR_RESPONSE_400,
    ERROR_RESPONSE_403,
    ERROR_RESPONSE_404,
    ERROR_RESPONSE_422,
)
from permissions import check_permissions
from workspaces.invitations import services as workspaces_invitations_services
from workspaces.invitations.api.validators import WorkspaceInvitationsValidator
from workspaces.invitations.models import WorkspaceInvitation
from workspaces.invitations.permissions import InvitationPermissionsCheck
from workspaces.invitations.serializers import (
    CreateWorkspaceInvitationsSerializer,
    PublicWorkspaceInvitationSerializer,
    WorkspaceInvitationSerializer,
)
from workspaces.invitations.services.exceptions import BadInvitationTokenError
from workspaces.workspaces.api import get_workspace_or_404

workspace_invit_router = Router()


##########################################################
# create workspace invitations
##########################################################


@workspace_invit_router.post(
    "/workspaces/{id}/invitations",
    url_name="workspace.invitations.create",
    summary="Create workspace invitations",
    response={
        200: CreateWorkspaceInvitationsSerializer,
        400: ERROR_RESPONSE_400,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def create_workspace_invitations(
    request,
    id: Path[B64UUID],
    form: WorkspaceInvitationsValidator,
) -> CreateWorkspaceInvitationsSerializer:
    """
    Create invitations to a workspace for a list of users (identified either by their username or their email).
    """
    workspace = await get_workspace_or_404(id=id)
    await check_permissions(
        permissions=InvitationPermissionsCheck.CREATE.value,
        user=request.user,
        obj=workspace,
    )

    return await workspaces_invitations_services.create_workspace_invitations(
        workspace=workspace,
        invitations=form.model_dump()["invitations"],
        invited_by=request.user,
    )


##########################################################
# list workspace invitations
##########################################################


@workspace_invit_router.get(
    "/workspaces/{id}/invitations",
    url_name="workspace.invitations.list",
    summary="List workspace pending invitations",
    response={
        200: list[WorkspaceInvitationSerializer],
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def list_workspace_invitations(
    request,
    id: Path[B64UUID],
) -> list[WorkspaceInvitation]:
    """
    List (pending) workspace invitations
    """
    workspace = await get_workspace_or_404(id)
    await check_permissions(
        permissions=InvitationPermissionsCheck.VIEW.value,
        user=request.user,
        obj=workspace,
    )

    return await workspaces_invitations_services.list_pending_workspace_invitations(
        workspace=workspace
    )


# ##########################################################
# # get workspace invitation
# ##########################################################


@workspace_invit_router.get(
    "/workspaces/invitations/{token}",
    url_name="workspace.invitations.get",
    summary="Get public information about a workspace invitation",
    response={
        200: PublicWorkspaceInvitationSerializer,
        400: ERROR_RESPONSE_400,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
    auth=None,
)
async def get_public_workspace_invitation(
    request, token: str
) -> PublicWorkspaceInvitationSerializer:
    """
    Get public information about a workspace invitation
    """
    try:
        invitation = (
            await workspaces_invitations_services.get_public_workspace_invitation(
                token=token
            )
        )
    except BadInvitationTokenError:
        raise ex.BadRequest("Invalid token")
    if not invitation:
        raise ex.NotFoundError("Invitation not found")

    return invitation


# ##########################################################
# # accept workspace invitation
# ##########################################################


@workspace_invit_router.post(
    "/workspaces/invitations/{token}/accept",
    url_name="workspace.invitations.accept",
    summary="Accept a workspace invitation using a token",
    response={
        200: WorkspaceInvitationSerializer,
        400: ERROR_RESPONSE_400,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
    },
    by_alias=True,
)
async def accept_workspace_invitation_by_token(
    request, token: str
) -> WorkspaceInvitation:
    """
    A user accepts a workspace invitation using an invitation token
    """
    try:
        invitation = await get_workspace_invitation_by_token_or_404(token=token)
    except BadInvitationTokenError:
        raise ex.BadRequest("Invalid token")

    await check_permissions(
        permissions=InvitationPermissionsCheck.ANSWER.value,
        user=request.user,
        obj=invitation,
    )

    return await workspaces_invitations_services.accept_workspace_invitation(
        invitation=invitation
    )


##########################################################
# misc
##########################################################


async def get_workspace_invitation_by_token_or_404(token: str) -> WorkspaceInvitation:
    invitation = await workspaces_invitations_services.get_workspace_invitation(
        token=token
    )
    if not invitation:
        raise ex.NotFoundError("Invitation does not exist")

    return invitation
