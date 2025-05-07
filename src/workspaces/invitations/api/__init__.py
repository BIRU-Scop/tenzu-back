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
from memberships.api.validators import InvitationsValidator, UpdateInvitationValidator
from memberships.services.exceptions import (
    BadInvitationTokenError,
    InvitationNonExistingUsernameError,
    OwnerRoleNotAuthorisedError,
)
from permissions import check_permissions
from workspaces.invitations import services as workspaces_invitations_services
from workspaces.invitations.models import WorkspaceInvitation
from workspaces.invitations.permissions import WorkspaceInvitationPermissionsCheck
from workspaces.invitations.serializers import (
    CreateInvitationsSerializer,
    PublicWorkspacePendingInvitationSerializer,
    WorkspaceInvitationSerializer,
)
from workspaces.workspaces.api import get_workspace_or_404

workspace_invit_router = Router()


##########################################################
# create workspace invitations
##########################################################


@workspace_invit_router.post(
    "/workspaces/{workspace_id}/invitations",
    url_name="workspace.invitations.create",
    summary="Create workspace invitations",
    response={
        200: CreateInvitationsSerializer,
        400: ERROR_RESPONSE_400,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def create_workspace_invitations(
    request,
    workspace_id: Path[B64UUID],
    form: InvitationsValidator,
) -> CreateInvitationsSerializer:
    """
    Create invitations to a workspace for a list of users (identified either by their username or their email), and the
    role they'll take in the workspace). In case of receiving several invitations for the same user, just the first
    role will be considered.
    """
    workspace = await get_workspace_or_404(workspace_id=workspace_id)
    await check_permissions(
        permissions=WorkspaceInvitationPermissionsCheck.CREATE.value,
        user=request.user,
        obj=workspace,
    )

    try:
        return await workspaces_invitations_services.create_workspace_invitations(
            workspace=workspace,
            invitations=form.model_dump()["invitations"],
            invited_by=request.user,
        )
    except InvitationNonExistingUsernameError as e:
        raise ex.BadRequest(str(e))
    except OwnerRoleNotAuthorisedError as e:
        raise ex.ForbiddenError(str(e))


##########################################################
# list workspace invitations
##########################################################


@workspace_invit_router.get(
    "/workspaces/{workspace_id}/invitations",
    url_name="workspace.invitations.list",
    summary="List workspace invitations",
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
    workspace_id: Path[B64UUID],
) -> list[WorkspaceInvitation]:
    """
    List (pending) workspace invitations
    """
    workspace = await get_workspace_or_404(workspace_id)
    await check_permissions(
        permissions=WorkspaceInvitationPermissionsCheck.VIEW.value,
        user=request.user,
        obj=workspace,
    )

    return await workspaces_invitations_services.list_workspace_invitations(
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
        200: PublicWorkspacePendingInvitationSerializer,
        400: ERROR_RESPONSE_400,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
    auth=None,
)
async def get_public_pending_workspace_invitation(
    request, token: str
) -> PublicWorkspacePendingInvitationSerializer:
    """
    Get public information about a pending workspace invitation
    """
    try:
        invitation = await workspaces_invitations_services.get_public_pending_workspace_invitation(
            token=token
        )
    except BadInvitationTokenError as e:
        raise ex.BadRequest(str(e))
    except WorkspaceInvitation.DoesNotExist as e:
        raise ex.NotFoundError("Invitation not found") from e

    return invitation


##########################################################
# resend workspace invitation
##########################################################


@workspace_invit_router.post(
    "/workspaces/{workspace_id}/invitations/{invitation_id}/resend",
    url_name="workspace.invitations.resend",
    summary="Resend workspace invitation",
    response={
        200: WorkspaceInvitationSerializer,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def resend_workspace_invitation(
    request,
    invitation_id: Path[B64UUID],
    workspace_id: Path[B64UUID],
) -> WorkspaceInvitation:
    """
    Resend invitation to a workspace
    """
    invitation = await get_workspace_invitation_by_id_or_404(
        workspace_id=workspace_id, invitation_id=invitation_id
    )
    await check_permissions(
        permissions=WorkspaceInvitationPermissionsCheck.CREATE.value,
        user=request.user,
        obj=invitation.workspace,
    )
    return await workspaces_invitations_services.resend_workspace_invitation(
        invitation=invitation, resent_by=request.user
    )


##########################################################
# revoke workspace invitation
##########################################################


@workspace_invit_router.post(
    "/workspaces/{workspace_id}/invitations/{invitation_id}/revoke",
    url_name="workspace.invitations.revoke",
    summary="Revoke workspace invitation",
    response={
        200: WorkspaceInvitationSerializer,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def revoke_workspace_invitation(
    request,
    invitation_id: Path[B64UUID],
    workspace_id: Path[B64UUID],
) -> WorkspaceInvitation:
    """
    Revoke invitation in a workspace.
    """
    invitation = await get_workspace_invitation_by_id_or_404(
        workspace_id=workspace_id, invitation_id=invitation_id
    )
    await check_permissions(
        permissions=WorkspaceInvitationPermissionsCheck.MODIFY.value,
        user=request.user,
        obj=invitation,
    )
    return await workspaces_invitations_services.revoke_workspace_invitation(
        invitation=invitation, revoked_by=request.user
    )


##########################################################
# deny workspace invitation
##########################################################


@workspace_invit_router.post(
    "/workspaces/{workspace_id}/invitations/deny",
    url_name="workspace.invitations.deny",
    summary="Deny workspace invitation for authenticated user",
    response={
        200: WorkspaceInvitationSerializer,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def deny_workspace_invitation_by_workspace(
    request, workspace_id: Path[B64UUID]
) -> WorkspaceInvitation:
    """
    An authenticated user denies a workspace invitation for themself.
    """
    await check_permissions(
        permissions=WorkspaceInvitationPermissionsCheck.ANSWER_SELF.value,
        user=request.user,
        obj=None,
    )
    invitation = await get_workspace_invitation_by_username_or_email_or_404(
        workspace_id=workspace_id, username_or_email=request.user.username
    )

    return await workspaces_invitations_services.deny_workspace_invitation(
        invitation=invitation
    )


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
    except BadInvitationTokenError as e:
        raise ex.BadRequest(str(e))

    await check_permissions(
        permissions=WorkspaceInvitationPermissionsCheck.ANSWER.value,
        user=request.user,
        obj=invitation,
    )

    return await workspaces_invitations_services.accept_workspace_invitation(
        invitation=invitation
    )


@workspace_invit_router.post(
    "/workspaces/{workspace_id}/invitations/accept",
    url_name="workspace.my.invitations.accept",
    summary="Accept a workspace invitation for authenticated users",
    response={
        200: WorkspaceInvitationSerializer,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def accept_workspace_invitation_by_workspace(
    request, workspace_id: Path[B64UUID]
) -> WorkspaceInvitation:
    """
    An authenticated user accepts a workspace invitation
    """
    await check_permissions(
        permissions=WorkspaceInvitationPermissionsCheck.ANSWER_SELF.value,
        user=request.user,
        obj=None,
    )
    invitation = await get_workspace_invitation_by_username_or_email_or_404(
        workspace_id=workspace_id, username_or_email=request.user.username
    )
    return await workspaces_invitations_services.accept_workspace_invitation(
        invitation=invitation
    )


##########################################################
# update workspace invitation
##########################################################


@workspace_invit_router.patch(
    "/workspaces/{workspace_id}/invitations/{invitation_id}",
    url_name="workspace.invitations.update",
    summary="Update workspace invitation",
    response={
        200: WorkspaceInvitationSerializer,
        403: ERROR_RESPONSE_403,
        404: ERROR_RESPONSE_404,
        422: ERROR_RESPONSE_422,
    },
    by_alias=True,
)
async def update_workspace_invitation(
    request,
    invitation_id: Path[B64UUID],
    workspace_id: Path[B64UUID],
    form: UpdateInvitationValidator,
) -> WorkspaceInvitation:
    """
    Update workspace invitation
    """
    invitation = await get_workspace_invitation_by_id_or_404(
        workspace_id=workspace_id, invitation_id=invitation_id
    )
    await check_permissions(
        permissions=WorkspaceInvitationPermissionsCheck.MODIFY.value,
        user=request.user,
        obj=invitation,
    )

    try:
        return await workspaces_invitations_services.update_workspace_invitation(
            invitation=invitation,
            role_slug=form.role_slug,
            user=request.user,
        )
    except OwnerRoleNotAuthorisedError as e:
        raise ex.ForbiddenError(str(e))


##########################################################
# misc
##########################################################


async def get_workspace_invitation_by_username_or_email_or_404(
    workspace_id: UUID, username_or_email: str
) -> WorkspaceInvitation:
    try:
        invitation = await workspaces_invitations_services.get_workspace_invitation_by_username_or_email(
            workspace_id=workspace_id, username_or_email=username_or_email
        )
    except WorkspaceInvitation.DoesNotExist as e:
        raise ex.NotFoundError("Invitation not found") from e

    return invitation


async def get_workspace_invitation_by_id_or_404(
    workspace_id: UUID, invitation_id: UUID
) -> WorkspaceInvitation:
    try:
        invitation = (
            await workspaces_invitations_services.get_workspace_invitation_by_id(
                workspace_id=workspace_id, invitation_id=invitation_id
            )
        )
    except WorkspaceInvitation.DoesNotExist as e:
        raise ex.NotFoundError("Invitation not found") from e

    return invitation


async def get_workspace_invitation_by_token_or_404(token: str) -> WorkspaceInvitation:
    try:
        invitation = await workspaces_invitations_services.get_workspace_invitation(
            token=token
        )
    except WorkspaceInvitation.DoesNotExist as e:
        raise ex.NotFoundError("Invitation does not exist") from e

    return invitation
